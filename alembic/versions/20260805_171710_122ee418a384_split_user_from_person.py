"""Split PlatformUser from Person

Revision ID: 122ee418a384
Revises: a89591b9197d
Create Date: 2026-08-05 17:17:10.942746


"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


import app.db.types

# revision identifiers, used by Alembic.
revision: str = "122ee418a384"
down_revision: Union[str, None] = "a89591b9197d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "activity",
    "agent",
    "annotation",
    "annotation_body",
    "asset",
    "brain_region",
    "brain_region_hierarchy",
    "contribution",
    "derivation",
    "entity",
    "etype_class",
    "etype_classification",
    "external_url",
    "ion",
    "ion_channel",
    "license",
    "measurement_annotation",
    "measurement_label",
    "mtype_class",
    "mtype_classification",
    "publication",
    "role",
    "scientific_artifact_external_url_link",
    "scientific_artifact_publication_link",
    "species",
    "strain",
]

# Persons referenced as created_by_id/updated_by_id that have no sub_id.
# Maps person.id -> sub_id to assign.
# Persons with an exact-name twin reuse the twin's sub_id; others get a fixed new UUID.
NULL_SUB_ID_MAPPING = {
    # exact-name twins: map to existing sub_id
    "d08f1bb2-531d-4460-b0ca-eef038c89b38": "0f358728-380a-4a19-8999-d44074e2f7b8",  # Darshan Mandge
    "8ebdbfe3-eb9a-4688-b9d3-9cca91551e82": "43d71718-a180-45ee-a757-7253d479c9d0",  # Eleftherios Zisis
    "5d300cb9-0706-4045-9efc-044a09325626": "80ec9244-5417-4ee4-ad35-e929c7ac1ecf",  # Pavlo Getta
    "0925e474-9b57-4bd1-b653-f8dd9b1f282e": "92b6868d-57f0-4674-895a-bc23c0bd0068",  # Gil Barrios
    "58feb075-c103-4166-9d0d-4608146e55e8": "598e1cd4-2d2f-4ba3-81ad-98853f14c006",  # Mathieu Chambon
    "e2520e33-e44c-4055-ac71-c4a66148a86f": "927bf2a8-a58e-44da-9ff1-e8f26c983a49",  # Jean-Denis Courcol
    "e7da77d1-00c7-4d26-99a9-2c2a12a4aef8": "d9e410ef-0ead-4274-8b85-f3d6dd59d262",  # Georges Khazen
    "e8624fab-5186-4e32-ae8d-7ee9770348a0": "9d7132d6-9719-4f06-9156-577e4967cee1",  # Kerem Kurban
    "4da4daeb-4f3f-4777-bad1-f45ae9500ec9": "481f8535-bfa4-40f2-87e2-705c299fb2ed",  # Bilal Meddah
    "8370e220-40f1-4697-bb68-09796f34b4d4": "8145e117-1ce6-45c7-ae09-126c332bc26d",  # Dries Verachtert
    "77a70061-8eb3-4fc8-885c-111a02a9970d": "23c0c3e4-209a-43ad-887f-a4a945746dd8",  # User Test Account
    # near-twins: map to existing sub_id
    "a8acb513-7c92-40dc-b4e0-88a9b9492f25": "7d592a0d-525f-4c24-8631-60a3bef19fe0",  # Aurelien Jaquier (near-twin of Aurélien Jaquier)
    "62c2d900-9b3f-4922-91bb-840cbabe20f3": "7d592a0d-525f-4c24-8631-60a3bef19fe0",  # Aurélien Jaquier (near-twin of Aurélien Jaquier)
    "d95bafc8-f2a4-427b-9cf4-bb99f4bea973": "63fb2ff4-7631-4355-b00a-5a94c3c42f47",  # Ilkan Kiliç (near-twin of Ilkan Kilic)
    "9770935e-c132-46a3-90c0-fbaaa88d09b0": "63fb2ff4-7631-4355-b00a-5a94c3c42f47",  # Ilkan Kilic (near-twin of Ilkan Kilic)
    # no twin: fixed new UUIDs
    "ec188c45-acbf-48de-acc8-85f57c28fd54": "45d4bfdc-d4e0-452c-8f39-d5b6f60480e3",  # Ivan Alcolea
    "81e220df-848b-4df7-8feb-994a81167346": "e3176334-d652-401b-bb0c-a7950bb67877",  # Boris Bergsma
    "d4c0dca8-b4c9-4755-8c9c-3adcf515a823": "fae35aeb-37d5-465b-96ab-526ff851f3c3",  # Nicolas Frank
    "3ff98ff3-87c5-4473-a7a8-3ee0761ebfd2": "0cd7c6c4-d58e-406b-9b2b-f06fdad03f2d",  # Nabil Alibou
    "5c6e4337-15ba-4bdd-9772-19d30e7a269f": "aa9398fe-2a26-4aef-8614-4f886dc6755d",  # h arikris
    "e89204e2-e816-4561-867e-5e15bc01bfce": "d9e289c0-c6d8-4085-a4a2-d69a31baf829",  # Leonardo Cristel
    "83844b40-ffa9-49f1-9c14-bc4a829e07b0": "c71e67b7-bd09-4584-8a53-3f0ebd6f5f01",  # Tanguy Damart
    "bd143fa9-b714-410c-a65d-7435c1066932": "96ce4b1d-a285-4784-bf1a-f7ae5abef89a",  # Cristina Gonzalez
    "4067c358-4ee2-47f8-9a94-e3e8ab73738f": "d48835e4-844c-4418-acdc-aac7949b5274",  # Anna-Kristin Kaufmann
    "82523e86-feac-4eb7-9c38-f519b91751da": "199a5651-e5ec-47e3-9971-cf46999c3829",  # Jonathan Lurie
    "cbd4d3e2-d4de-49ef-83f0-be4e80371eb9": "d9515759-e677-4219-a1e9-4f0526ed8874",  # Patricia Lurie
    "6a27e0df-cbf8-4544-b215-4e76e4c11ab2": "fdb8ac5d-ecf7-4fad-847c-954e157f1962",  # Sarah Mouffok
    "ffed9235-288b-4781-ae66-267594c9c950": "af7f8fea-8f0d-4766-8750-a17e1b8d88b6",  # Ayima Okeeva
    "cf1822ff-bc68-4778-ab49-1044d5e34124": "1b4bedf6-b0df-4bc1-8055-b0da12ae490f",  # Niccolò Ricardi
    "f4767f26-2943-45b2-b21d-ea3bf63f23d0": "0a2682ce-c703-4e7b-9e92-a0674d8ae17e",  # service-account-bbp-dke-bluebrainatlas-sa
    "7f81375e-ecc1-4b63-8773-3e847d718d73": "c01782af-8fd2-4fd2-8908-cb3e11349da9",  # service-account-bbp-dke-data-pipelines-sa
    "97eeab64-ca2c-46bc-9d3f-d983c34c769f": "32e6ac45-7c9a-4e83-bb5c-fd696f68e049",  # service-account-nexus-sa
    "59cc60b1-7604-44b4-a736-95c3e652c71a": "86223f2d-f02d-48b5-86d4-2ea625f03c75",  # service-account-obp-singlecell-uploader-sa
    "e06f291b-2a83-4af8-95c4-4a4eb3172062": "b146bf10-db24-4c77-b67a-9777cb111b7b",  # service-account-obp-virtuallab-sa
    "74667bff-e202-449d-a964-3a295a9ac6de": "bd8a6398-2220-4c45-b006-305dc2890458",  # service-brain-modeling-ontology-ci-cd
    "fec3f6b3-2e8d-4b8a-8f54-f8ceacaab39e": "aef006e5-dda3-40bc-aa14-f4176fa28efb",  # Mohameth François Sy
    "cd613e30-d8f1-4adf-91b7-584a2265b1f5": "142495ee-7a08-435d-8220-bd7a590a7c85",  # OBI
}


def _drop_fks(ref: str) -> None:
    for table in TABLES:
        for col in ("created_by_id", "updated_by_id"):
            op.drop_constraint(op.f(f"fk_{table}_{col}_{ref}"), table, type_="foreignkey")


def _create_fks(ref: str) -> None:
    for table in TABLES:
        for col in ("created_by_id", "updated_by_id"):
            op.create_foreign_key(op.f(f"fk_{table}_{col}_{ref}"), table, ref, [col], ["id"])


def upgrade() -> None:
    # Disable statement and lock timeouts: the UPDATE loop over large tables triggers
    # FK key-share locks that can exceed the defaults set in env.py CONNECTION_SETTINGS.
    op.execute("SET statement_timeout = 0")
    op.execute("SET lock_timeout = 0")
    op.create_table(
        "platform_user",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pref_label", sa.String(), nullable=False),
        sa.Column(
            "creation_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("statement_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "update_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("statement_timestamp()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_user")),
    )
    op.create_index(
        op.f("ix_platform_user_creation_date"), "platform_user", ["creation_date"], unique=False
    )
    op.create_index(
        op.f("ix_platform_user_pref_label"), "platform_user", ["pref_label"], unique=False
    )
    # Drop the unique index on person.sub_id before backfilling duplicates
    op.drop_index(op.f("ix_person_sub_id"), table_name="person")
    # Save original person_id -> sub_id mapping before backfilling duplicates.
    # Used by a later migration to re-add Person.sub_id as FK to platform_user.
    op.execute("""
        CREATE TABLE _person_sub_id_mapping AS
        SELECT id AS person_id, sub_id
        FROM person
        WHERE sub_id IS NOT NULL
    """)
    # Backfill sub_id for persons that are referenced as created_by_id/updated_by_id but have none
    values = ", ".join(
        f"('{person_id}'::uuid, '{sub_id}'::uuid)"
        for person_id, sub_id in NULL_SUB_ID_MAPPING.items()
    )
    op.execute(f"""
        UPDATE person SET sub_id = m.new_sub_id
        FROM (VALUES {values}) AS m(person_id, new_sub_id)
        WHERE person.id = m.person_id
          AND person.sub_id IS NULL
    """)
    # Populate user table from all persons that now have a sub_id, one row per distinct sub_id
    op.execute("""
        INSERT INTO platform_user (id, pref_label, creation_date, update_date)
        SELECT DISTINCT ON (p.sub_id)
            p.sub_id, a.pref_label, a.creation_date, a.update_date
        FROM person p
        JOIN agent a ON a.id = p.id
        WHERE p.sub_id IS NOT NULL
        ORDER BY p.sub_id
    """)
    # Drop agent FKs before remapping the columns
    _drop_fks("agent")
    # Remap created_by_id / updated_by_id on all tables from agent.id to person.sub_id
    for table in TABLES:
        op.execute(f"""
            UPDATE "{table}" t
            SET created_by_id = p_c.sub_id,
                updated_by_id = p_u.sub_id
            FROM person p_c, person p_u
            WHERE p_c.id = t.created_by_id
              AND p_u.id = t.updated_by_id
        """)
    _create_fks("platform_user")
    op.drop_column("person", "sub_id")


def downgrade() -> None:
    # Data migration is not reversed: the sub_id uniqueness constraint on person cannot be
    # restored after merging duplicate persons (twins/near-twins) into a single user.
    # FK columns (created_by_id/updated_by_id) will point to user.id values after downgrade,
    # but the agent FK constraints are restored so the schema is valid for further migrations.
    _drop_fks("platform_user")
    _create_fks("agent")
    op.add_column("person", sa.Column("sub_id", sa.UUID(), autoincrement=False, nullable=True))
    op.create_index(op.f("ix_person_sub_id"), "person", ["sub_id"], unique=True)
    op.drop_index(op.f("ix_platform_user_pref_label"), table_name="platform_user")
    op.drop_index(op.f("ix_platform_user_creation_date"), table_name="platform_user")
    op.drop_table("platform_user")
