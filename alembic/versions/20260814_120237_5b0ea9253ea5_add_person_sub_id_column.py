"""Add Person.sub_id column

Revision ID: 5b0ea9253ea5
Revises: 1695b8e6508c
Create Date: 2026-08-14 12:02:37.770855

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import app.db.types

# revision identifiers, used by Alembic.
revision: str = "5b0ea9253ea5"
down_revision: Union[str, None] = "1695b8e6508c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Persons imported from Nexus that had no Keycloak sub_id.
# The split migration assigned them synthetic PlatformUser ids for FK integrity.
# Maps person_id -> synthetic platform_user.id (same as in the split migration).
_SYNTHETIC_SUB_ID_MAPPING = {
    "ec188c45-acbf-48de-acc8-85f57c28fd54": "45d4bfdc-d4e0-452c-8f39-d5b6f60480e3",
    "81e220df-848b-4df7-8feb-994a81167346": "e3176334-d652-401b-bb0c-a7950bb67877",
    "d4c0dca8-b4c9-4755-8c9c-3adcf515a823": "fae35aeb-37d5-465b-96ab-526ff851f3c3",
    "3ff98ff3-87c5-4473-a7a8-3ee0761ebfd2": "0cd7c6c4-d58e-406b-9b2b-f06fdad03f2d",
    "5c6e4337-15ba-4bdd-9772-19d30e7a269f": "aa9398fe-2a26-4aef-8614-4f886dc6755d",
    "e89204e2-e816-4561-867e-5e15bc01bfce": "d9e289c0-c6d8-4085-a4a2-d69a31baf829",
    "83844b40-ffa9-49f1-9c14-bc4a829e07b0": "c71e67b7-bd09-4584-8a53-3f0ebd6f5f01",
    "bd143fa9-b714-410c-a65d-7435c1066932": "96ce4b1d-a285-4784-bf1a-f7ae5abef89a",
    "4067c358-4ee2-47f8-9a94-e3e8ab73738f": "d48835e4-844c-4418-acdc-aac7949b5274",
    "82523e86-feac-4eb7-9c38-f519b91751da": "199a5651-e5ec-47e3-9971-cf46999c3829",
    "cbd4d3e2-d4de-49ef-83f0-be4e80371eb9": "d9515759-e677-4219-a1e9-4f0526ed8874",
    "6a27e0df-cbf8-4544-b215-4e76e4c11ab2": "fdb8ac5d-ecf7-4fad-847c-954e157f1962",
    "ffed9235-288b-4781-ae66-267594c9c950": "af7f8fea-8f0d-4766-8750-a17e1b8d88b6",
    "cf1822ff-bc68-4778-ab49-1044d5e34124": "1b4bedf6-b0df-4bc1-8055-b0da12ae490f",
    "f4767f26-2943-45b2-b21d-ea3bf63f23d0": "0a2682ce-c703-4e7b-9e92-a0674d8ae17e",
    "7f81375e-ecc1-4b63-8773-3e847d718d73": "c01782af-8fd2-4fd2-8908-cb3e11349da9",
    "97eeab64-ca2c-46bc-9d3f-d983c34c769f": "32e6ac45-7c9a-4e83-bb5c-fd696f68e049",
    "59cc60b1-7604-44b4-a736-95c3e652c71a": "86223f2d-f02d-48b5-86d4-2ea625f03c75",
    "e06f291b-2a83-4af8-95c4-4a4eb3172062": "b146bf10-db24-4c77-b67a-9777cb111b7b",
    "74667bff-e202-449d-a964-3a295a9ac6de": "bd8a6398-2220-4c45-b006-305dc2890458",
    "fec3f6b3-2e8d-4b8a-8f54-f8ceacaab39e": "aef006e5-dda3-40bc-aa14-f4176fa28efb",
    "cd613e30-d8f1-4adf-91b7-584a2265b1f5": "142495ee-7a08-435d-8220-bd7a590a7c85",
}


def upgrade() -> None:
    op.add_column("person", sa.Column("sub_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_person_sub_id"), "person", ["sub_id"], unique=True)
    op.create_foreign_key(
        op.f("fk_person_sub_id_platform_user"), "person", "platform_user", ["sub_id"], ["id"]
    )
    # Populate sub_id from the mapping table saved by the split_user_from_person migration
    connection = op.get_bind()
    has_mapping_table = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables"
            "  WHERE table_name = '_person_sub_id_mapping'"
            ")"
        )
    ).scalar()
    if has_mapping_table:
        op.execute("""
            UPDATE person p
            SET sub_id = m.sub_id
            FROM _person_sub_id_mapping m
            WHERE p.id = m.person_id
        """)
    # Link persons that had no original sub_id to their synthetic PlatformUser
    if _SYNTHETIC_SUB_ID_MAPPING:
        values = ", ".join(
            f"('{person_id}'::uuid, '{sub_id}'::uuid)"
            for person_id, sub_id in _SYNTHETIC_SUB_ID_MAPPING.items()
        )
        op.execute(f"""
            UPDATE person p
            SET sub_id = m.sub_id
            FROM (VALUES {values}) AS m(person_id, sub_id)
            WHERE p.id = m.person_id
              AND p.sub_id IS NULL
        """)
    # Create Person records for PlatformUsers that still have no corresponding Person.
    # This covers users created after the split migration removed sub_id (staging only).
    op.execute("""
        WITH new_persons AS (
            SELECT gen_random_uuid() AS person_id, pu.id AS sub_id,
                   pu.pref_label, pu.creation_date, pu.update_date
            FROM platform_user pu
            WHERE NOT EXISTS (
                SELECT 1 FROM person p WHERE p.sub_id = pu.id
            )
        ),
        inserted_agents AS (
            INSERT INTO agent (id, type, pref_label, created_by_id, updated_by_id,
                               creation_date, update_date)
            SELECT person_id, 'person', pref_label, sub_id, sub_id,
                   creation_date, update_date
            FROM new_persons
            RETURNING id
        )
        INSERT INTO person (id, sub_id)
        SELECT np.person_id, np.sub_id
        FROM new_persons np
    """)


def downgrade() -> None:
    op.drop_constraint(op.f("fk_person_sub_id_platform_user"), "person", type_="foreignkey")
    op.drop_index(op.f("ix_person_sub_id"), table_name="person")
    op.drop_column("person", "sub_id")
