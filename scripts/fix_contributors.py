"""Consolidate duplicate / mis-typed contributor agents in entitycore.

Some entities list the wrong contributor agent, producing duplicate-looking
contributors:

- "OBI" (a *person* agent auto-created for the shared OBI login) instead of the
  Open Brain Institute *organization* agent; and
- the same real person appearing as several *person* agents (e.g. a
  Keycloak-linked record plus loginless records created by data imports).

Both are the same underlying operation: repoint every contribution from one or
more *source* agents onto a single *target* agent, then drop the exact
duplicates that would otherwise collide.

Safety (applies to every subcommand):
- Dry-run by default. Pass --apply to write changes.
- Runs in a single transaction; rolls back on any error.
- Only repoints rows that do NOT violate the
  unique_contribution_1 (entity_id, role_id, agent_id) constraint.
- Deletes only exact duplicates (an equivalent contribution from the target
  already exists on the same entity + role).
- No-op when the target or every source is missing.
- Never deletes agent rows (only contribution rows). Removing the leftover
  duplicate *agents* is intentionally out of scope; do that separately once the
  contributions have been consolidated and verified.

Usage (from the repo root; DB connection comes from the app settings / env):

    # OBI person -> Open Brain Institute organization (label-based, env-agnostic)
    uv run python -m scripts.fix_contributors merge-obi            # dry-run
    uv run python -m scripts.fix_contributors merge-obi --apply

    # Merge duplicate person agents into a canonical one (explicit UUIDs).
    # The canonical/target differs per environment, so ids are always explicit.
    uv run python -m scripts.fix_contributors merge-persons \\
        --target <canonical-agent-uuid> \\
        --source <duplicate-agent-uuid> [--source <another-duplicate-uuid> ...]
    # add --apply to persist
"""

import logging  # noqa: INP001
import uuid

import click
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.model import Agent, Contribution, Organization, Person
from app.db.session import configure_database_session_manager

L = logging.getLogger("fix_contributors")

DEFAULT_PERSON_LABEL = "OBI"
DEFAULT_ORG_LABEL = "Open Brain Institute, Lausanne, Switzerland"


def _target_dup_clause(target_id: uuid.UUID):
    """A contribution from the target already exists on the same (entity_id, role_id)."""
    c2 = sa.orm.aliased(Contribution)
    return sa.exists().where(
        c2.entity_id == Contribution.entity_id,
        c2.role_id == Contribution.role_id,
        c2.agent_id == target_id,
    )


def merge_contributions(
    db: Session,
    *,
    source_ids: list[uuid.UUID],
    target_id: uuid.UUID,
    apply: bool,
) -> tuple[int, int]:
    """Repoint contributions from source agents onto the target agent.

    Returns (repointed_count, deleted_count). Collision-safe: rows that would
    duplicate an existing target contribution on (entity_id, role_id) are deleted
    instead of repointed. Does not touch agent rows.
    """
    source_ids = [s for s in source_ids if s != target_id]
    if not source_ids:
        L.info("No source agents to merge (after excluding the target).")
        return (0, 0)

    dup_exists = _target_dup_clause(target_id)

    to_repoint = (
        db.execute(
            sa.select(Contribution).where(
                Contribution.agent_id.in_(source_ids),
                sa.not_(dup_exists),
            )
        )
        .scalars()
        .all()
    )
    to_delete = (
        db.execute(
            sa.select(Contribution).where(
                Contribution.agent_id.in_(source_ids),
                dup_exists,
            )
        )
        .scalars()
        .all()
    )

    L.info("Target agent: %s", target_id)
    L.info("Source agents: %s", ", ".join(str(s) for s in source_ids))
    L.info("Contributions to repoint: %d", len(to_repoint))
    L.info("Duplicate contributions to delete: %d", len(to_delete))
    for c in to_repoint:
        L.info("  repoint contribution %s (entity=%s role=%s)", c.id, c.entity_id, c.role_id)
    for c in to_delete:
        L.info("  delete   contribution %s (entity=%s role=%s)", c.id, c.entity_id, c.role_id)

    if not apply:
        L.info("Dry-run: no changes written. Re-run with --apply to persist.")
        return (len(to_repoint), len(to_delete))

    for c in to_repoint:
        c.agent_id = target_id
    for c in to_delete:
        db.delete(c)

    db.flush()
    L.info("Applied: %d repointed, %d deleted.", len(to_repoint), len(to_delete))
    return (len(to_repoint), len(to_delete))


def _resolve_person_by_label(db: Session, pref_label: str) -> Person | None:
    # Querying the polymorphic subclass restricts to type == 'person'.
    return db.execute(
        sa.select(Person).where(Person.pref_label == pref_label)
    ).scalar_one_or_none()


def _resolve_org_by_label(db: Session, pref_label: str) -> Organization | None:
    return db.execute(
        sa.select(Organization).where(Organization.pref_label == pref_label)
    ).scalar_one_or_none()


def _load_agent(db: Session, agent_id: uuid.UUID) -> Agent | None:
    return db.get(Agent, agent_id)


@click.group()
def cli() -> None:
    """Contributor consolidation tools (dry-run by default)."""


@cli.command("merge-obi")
@click.option("--person-label", default=DEFAULT_PERSON_LABEL, show_default=True)
@click.option("--org-label", default=DEFAULT_ORG_LABEL, show_default=True)
@click.option("--apply", is_flag=True, default=False, help="Persist changes (default: dry-run).")
def merge_obi(person_label: str, org_label: str, apply: bool) -> None:
    """Repoint the 'OBI' person's contributions onto the Open Brain Institute org."""
    manager = configure_database_session_manager()
    try:
        with manager.session() as db:
            person = _resolve_person_by_label(db, person_label)
            org = _resolve_org_by_label(db, org_label)
            if person is None:
                L.info("No person agent %r found; nothing to do.", person_label)
                return
            if org is None:
                L.info("No organization agent %r found; nothing to do.", org_label)
                return
            L.info("Source person: %s (%s)", person.pref_label, person.id)
            L.info("Target org:    %s (%s)", org.pref_label, org.id)
            merge_contributions(db, source_ids=[person.id], target_id=org.id, apply=apply)
    finally:
        manager.close()


@cli.command("merge-persons")
@click.option("--target", "target", type=click.UUID, required=True, help="Canonical agent UUID.")
@click.option(
    "--source",
    "sources",
    type=click.UUID,
    multiple=True,
    required=True,
    help="Duplicate agent UUID to merge into the target (repeatable).",
)
@click.option("--apply", is_flag=True, default=False, help="Persist changes (default: dry-run).")
def merge_persons(target: uuid.UUID, sources: tuple[uuid.UUID, ...], apply: bool) -> None:
    """Merge duplicate person agents (explicit UUIDs) into a canonical target.

    The canonical target differs per environment (and the same UUID can be a
    duplicate in one environment and canonical in another), so UUIDs are always
    passed explicitly rather than inferred.
    """
    manager = configure_database_session_manager()
    try:
        with manager.session() as db:
            target_agent = _load_agent(db, target)
            if target_agent is None:
                L.info("Target agent %s not found; nothing to do.", target)
                return
            L.info("Target agent: %s (%s)", target_agent.pref_label, target_agent.id)
            for s in sources:
                src = _load_agent(db, s)
                if src is None:
                    L.warning("Source agent %s not found; skipping.", s)
                else:
                    L.info("Source agent: %s (%s)", src.pref_label, src.id)
            merge_contributions(db, source_ids=list(sources), target_id=target, apply=apply)
    finally:
        manager.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cli()
