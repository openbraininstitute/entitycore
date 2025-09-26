import functools
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import NamedTuple
from unittest.mock import ANY
from uuid import UUID

import sqlalchemy as sa
from httpx import Headers
from pydantic import TypeAdapter
from starlette.testclient import TestClient

from app.db.model import (
    BrainRegion,
    BrainRegionHierarchy,
    CellMorphology,
    Contribution,
    ElectricalCellRecording,
    ElectricalRecordingStimulus,
    Entity,
    ETypeClass,
    ETypeClassification,
    IonChannelRecording,
    MTypeClass,
    MTypeClassification,
    Person,
    Species,
    Strain,
    Subject,
)
from app.db.types import EntityType
from app.routers.asset import EntityRoute
from app.utils.uuid import create_uuid

DateTimeAdapter = TypeAdapter(datetime)

TEST_DATA_DIR = Path(__file__).parent / "data"

ADMIN_SUB_ID = "00000000-0000-0000-0000-000000000000"
USER_SUB_ID_1 = "00000000-0000-0000-0000-000000000001"
USER_SUB_ID_2 = "00000000-0000-0000-0000-000000000002"

TOKEN_ADMIN = "I'm admin"  # noqa: S105
TOKEN_USER_1 = "I'm user 1"  # noqa: S105
TOKEN_USER_2 = "I'm user 2"  # noqa: S105

AUTH_HEADER_ADMIN = {"Authorization": f"Bearer {TOKEN_ADMIN}"}
AUTH_HEADER_USER_1 = {"Authorization": f"Bearer {TOKEN_USER_1}"}
AUTH_HEADER_USER_2 = {"Authorization": f"Bearer {TOKEN_USER_2}"}

VIRTUAL_LAB_ID = "9c6fba01-2c6f-4eac-893f-f0dc665605c5"
PROJECT_ID = "ee86d4a0-eaca-48ca-9788-ddc450250b15"
UNRELATED_VIRTUAL_LAB_ID = "99999999-2c6f-4eac-893f-f0dc665605c5"
UNRELATED_PROJECT_ID = "66666666-eaca-48ca-9788-ddc450250b15"

MISSING_ID = "12345678-1234-5678-1234-567812345678"
MISSING_ID_COMPACT = MISSING_ID.replace("-", "")

PROJECT_HEADERS = {
    "virtual-lab-id": VIRTUAL_LAB_ID,
    "project-id": PROJECT_ID,
}
UNRELATED_PROJECT_HEADERS = {
    "virtual-lab-id": UNRELATED_VIRTUAL_LAB_ID,
    "project-id": UNRELATED_PROJECT_ID,
}

ROUTES = {
    CellMorphology: "/cell-morphology",
    ElectricalCellRecording: "/electrical-cell-recording",
    IonChannelRecording: "/ion-channel-recording",
}


class ClientProxy:
    """Proxy TestClient to pass default headers without creating a new instance.

    This can be used to avoid running the lifespan event multiple times.
    """

    def __init__(self, client: TestClient, headers: dict | None = None) -> None:
        self._client = client
        self._headers = headers
        self._methods = {"request", "get", "options", "head", "post", "put", "patch", "delete"}

    def __getattr__(self, name: str):
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, headers=None, **kwargs):
                merged_headers = Headers(self._headers)
                merged_headers.update(headers)
                return f(*args, headers=merged_headers, **kwargs)

            return wrapper

        method = getattr(self._client, name)
        return decorator(method) if name in self._methods else method


class ClientProxies(NamedTuple):
    user_1: ClientProxy
    user_2: ClientProxy
    no_project: ClientProxy
    admin: ClientProxy


def create_cell_morphology_id(
    client,
    subject_id,
    brain_region_id,
    name="Test Morphology Name",
    description="Test Morphology Description",
    *,
    authorized_public: bool = False,
):
    response = client.post(
        ROUTES[CellMorphology],
        json={
            "name": name,
            "description": description,
            "brain_region_id": str(brain_region_id),
            "subject_id": str(subject_id),
            "location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": ["Test Legacy ID"],
            "authorized_public": authorized_public,
        },
    )

    assert response.status_code == 200
    return response.json()["id"]


def add_db(db, row):
    """Add one row to the db and commit the transaction."""
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def add_all_db(db, rows, *, same_transaction=False):
    """Add all the rows to the db and commit the transaction.

    If same_transaction is True, all records are inserted in the same transaction,
    and the creation_date and update_date might be always the same.
    """
    if same_transaction:
        db.add_all(rows)
        db.commit()
    else:
        for row in rows:
            db.add(row)
            db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def assert_response(response, expected_status_code=200):
    assert response.status_code == expected_status_code, (
        f"Request {response.request.method} {response.request.url}: "
        f"expected={expected_status_code}, actual={response.status_code}, "
        f"content={response.content}"
    )


def assert_request(client_method, *, expected_status_code=200, **kwargs):
    response = client_method(**kwargs)
    assert_response(response, expected_status_code=expected_status_code)
    return response


def create_hiearchy_name(
    db, name: str, created_by_id: uuid.UUID, updated_by_id: uuid.UUID | None = None
):
    row = BrainRegionHierarchy(
        name=name, created_by_id=created_by_id, updated_by_id=updated_by_id or created_by_id
    )
    return add_db(db, row)


def create_brain_region(
    db,
    hierarchy_id,
    annotation_value: int,
    name: str,
    created_by_id: uuid.UUID,
    parent_id: uuid.UUID | None = None,
    updated_by_id: uuid.UUID | None = None,
):
    row = BrainRegion(
        annotation_value=annotation_value,
        acronym=f"acronym{annotation_value}",
        name=name,
        color_hex_triplet="FF0000",
        parent_structure_id=parent_id,
        hierarchy_id=hierarchy_id,
        created_by_id=created_by_id,
        updated_by_id=created_by_id or updated_by_id,
        embedding=1536 * [0.1],
    )
    return add_db(db, row)


def create_mtype(db, pref_label: str, created_by_id: uuid.UUID, alt_label=None, definition=None):
    return add_db(
        db,
        MTypeClass(
            pref_label=pref_label,
            alt_label=alt_label or pref_label,
            definition=definition or "",
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        ),
    )


def create_mtype_classification(
    db,
    *,
    entity_id: uuid.UUID,
    mtype_class_id: uuid.UUID,
    created_by_id: uuid.UUID,
    authorized_public: bool = False,
    authorized_project_id: uuid.UUID = PROJECT_ID,
):
    return add_db(
        db,
        MTypeClassification(
            entity_id=entity_id,
            mtype_class_id=mtype_class_id,
            authorized_public=authorized_public,
            authorized_project_id=authorized_project_id,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        ),
    )


def create_etype(db, pref_label: str, created_by_id: uuid.UUID, alt_label=None, definition=None):
    return add_db(
        db,
        ETypeClass(
            pref_label=pref_label,
            alt_label=alt_label or pref_label,
            definition=definition or "",
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        ),
    )


def create_etype_classification(
    db,
    *,
    entity_id: uuid.UUID,
    etype_class_id: uuid.UUID,
    created_by_id: uuid.UUID,
    authorized_public: bool = False,
    authorized_project_id: uuid.UUID = PROJECT_ID,
):
    return add_db(
        db,
        ETypeClassification(
            entity_id=entity_id,
            etype_class_id=etype_class_id,
            authorized_public=authorized_public,
            authorized_project_id=authorized_project_id,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        ),
    )


def create_electrical_recording_stimulus_id(db, recording_id, created_by_id):
    return add_db(
        db,
        ElectricalRecordingStimulus(
            name="protocol",
            description="protocol-description",
            dt=0.1,
            injection_type="current_clamp",
            shape="sinusoidal",
            start_time=0.0,
            end_time=1.0,
            recording_id=recording_id,
            authorized_public=False,
            authorized_project_id=PROJECT_ID,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        ),
    ).id


def create_electrical_cell_recording_id(client, json_data):
    result = assert_request(client.post, url=ROUTES[ElectricalCellRecording], json=json_data).json()
    return uuid.UUID(result["id"])


def create_electrical_cell_recording_db(db, client, json_data):
    trace_id = create_electrical_cell_recording_id(client, json_data)
    return db.get(ElectricalCellRecording, trace_id)


def create_electrical_cell_recording_id_with_assets(db, client, tmp_path, json_data):
    trace_id = create_electrical_cell_recording_id(client, json_data)

    trace = db.get(ElectricalCellRecording, trace_id)

    # add two protocols that refer to it
    create_electrical_recording_stimulus_id(db, trace_id, created_by_id=trace.created_by_id)
    create_electrical_recording_stimulus_id(db, trace_id, created_by_id=trace.created_by_id)

    filepath = tmp_path / "trace.nwb"
    filepath.write_bytes(b"trace")

    # add an asset too
    upload_entity_asset(
        client=client,
        entity_id=trace_id,
        entity_type=EntityType.electrical_cell_recording,
        files={"file": ("my-trace.nwb", filepath.read_bytes(), "application/nwb")},
        label="nwb",
    )

    # add an etype
    etype = create_etype(
        db,
        pref_label="etype-pref-label",
        alt_label="etype-alt-label",
        definition="etype-definition",
        created_by_id=trace.created_by_id,
    )
    create_etype_classification(
        db,
        entity_id=trace_id,
        etype_class_id=etype.id,
        created_by_id=trace.created_by_id,
        authorized_public=False,
        authorized_project_id=PROJECT_ID,
    )

    return trace_id


def create_ion_channel_recording_id(client, json_data):
    result = assert_request(client.post, url=ROUTES[IonChannelRecording], json=json_data).json()
    return uuid.UUID(result["id"])


def create_ion_channel_recording_db(db, client, json_data):
    trace_id = create_ion_channel_recording_id(client, json_data)
    return db.get(IonChannelRecording, trace_id)


def create_ion_channel_recording_id_with_assets(db, client, tmp_path, json_data):
    trace_id = create_ion_channel_recording_id(client, json_data)

    trace = db.get(IonChannelRecording, trace_id)

    # add two protocols that refer to it
    create_electrical_recording_stimulus_id(db, trace_id, created_by_id=trace.created_by_id)
    create_electrical_recording_stimulus_id(db, trace_id, created_by_id=trace.created_by_id)

    filepath = tmp_path / "trace.nwb"
    filepath.write_bytes(b"trace")

    # add an asset too
    upload_entity_asset(
        client=client,
        entity_id=trace_id,
        entity_type=EntityType.ion_channel_recording,
        files={"file": ("my-trace.nwb", filepath.read_bytes(), "application/nwb")},
        label="nwb",
    )

    return trace_id


def check_missing(route, client):
    assert_request(
        client.get,
        url=f"{route}/{MISSING_ID}",
        expected_status_code=404,
    )
    assert_request(
        client.get,
        url=f"{route}/{MISSING_ID_COMPACT}",
        expected_status_code=404,
    )
    assert_request(
        client.get,
        url=f"{route}/42424242",
        expected_status_code=422,
    )
    assert_request(
        client.get,
        url=f"{route}/notanumber",
        expected_status_code=422,
    )


def check_pagination(route, client, constructor_func):
    for i in range(3):
        constructor_func(
            name=f"name-{i}",
            description=f"description-{i}",
        )

    response = assert_request(
        client.get,
        url=route,
        params={"page_size": 2},
    )
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 2


def check_authorization(route, client_user_1, client_user_2, client_no_project, json_data):
    """Check the authorization when trying to access the entities.

    Created entities:

    public_u1_0 (PROJECT_ID)
    public_u2_0 (UNRELATED_PROJECT_ID)
    private_u2_0 (UNRELATED_PROJECT_ID)
    private_u1_0 (PROJECT_ID)
    private_u1_1 (PROJECT_ID)
    """
    # create the entities
    public_u1_0 = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"name": "Public u1/0", "authorized_public": True},
    ).json()
    assert public_u1_0["authorized_public"] is True
    assert public_u1_0["authorized_project_id"] == PROJECT_ID

    public_u2_0 = assert_request(
        client_user_2.post,
        url=route,
        json=json_data | {"name": "Public u2/0", "authorized_public": True},
    ).json()
    assert public_u2_0["authorized_public"] is True
    assert public_u2_0["authorized_project_id"] == UNRELATED_PROJECT_ID

    private_u2_0 = assert_request(
        client_user_2.post, url=route, json=json_data | {"name": "Private u2/0"}
    ).json()
    assert private_u2_0["authorized_public"] is False
    assert private_u2_0["authorized_project_id"] == UNRELATED_PROJECT_ID

    private_u1_0 = assert_request(
        client_user_1.post, url=route, json=json_data | {"name": "Private u1/0"}
    ).json()
    assert private_u1_0["authorized_public"] is False
    assert private_u1_0["authorized_project_id"] == PROJECT_ID

    private_u1_1 = assert_request(
        client_user_1.post, url=route, json=json_data | {"name": "Private u1/1"}
    ).json()
    assert private_u1_1["authorized_public"] is False
    assert private_u1_1["authorized_project_id"] == PROJECT_ID

    # only return results that matches the desired project, and public ones
    data = assert_request(client_user_1.get, url=route).json()["data"]
    assert len(data) == 4
    assert {row["id"] for row in data} == {
        public_u1_0["id"],
        public_u2_0["id"],
        private_u1_0["id"],
        private_u1_1["id"],
    }

    # cannot access the private entity of the other user
    assert_request(
        client_user_1.get,
        url=f"{route}/{private_u2_0['id']}",
        expected_status_code=404,
    )

    # client_no_project can get public entities only
    data = assert_request(client_no_project.get, url=route).json()["data"]
    assert len(data) == 2
    assert {row["id"] for row in data} == {
        public_u1_0["id"],
        public_u2_0["id"],
    }

    # client_user_1 wants only public results
    data = assert_request(
        client_user_1.get,
        url=route,
        params={"authorized_public": True},
    ).json()["data"]
    assert len(data) == 2
    assert {row["id"] for row in data} == {public_u1_0["id"], public_u2_0["id"]}

    # client_user_1 wants only private (and accessible) results
    data = assert_request(
        client_user_1.get,
        url=route,
        params={"authorized_public": False},
    ).json()["data"]
    assert len(data) == 2
    assert {row["id"] for row in data} == {private_u1_0["id"], private_u1_1["id"]}

    # client_user_1 wants only their own entities (private or public)
    data = assert_request(
        client_user_1.get,
        url=route,
        params={"authorized_project_id": PROJECT_ID},
    ).json()["data"]
    assert len(data) == 3
    assert {row["id"] for row in data} == {
        public_u1_0["id"],
        private_u1_0["id"],
        private_u1_1["id"],
    }

    # client_user_1 can get entities in other projects only if they are public
    data = assert_request(
        client_user_1.get,
        url=route,
        params={"authorized_project_id": UNRELATED_PROJECT_ID},
    ).json()["data"]
    assert len(data) == 1
    assert {row["id"] for row in data} == {public_u2_0["id"]}

    # client_user_1 can get entities in other projects only if they are public (again)
    data = assert_request(
        client_user_1.get,
        url=route,
        params={"authorized_public": True, "authorized_project_id": UNRELATED_PROJECT_ID},
    ).json()["data"]
    assert len(data) == 1
    assert {row["id"] for row in data} == {public_u2_0["id"]}

    # client_user_1 can get entities in other projects only if they are public (no results)
    data = assert_request(
        client_user_1.get,
        url=route,
        params={"authorized_public": False, "authorized_project_id": UNRELATED_PROJECT_ID},
    ).json()["data"]
    assert len(data) == 0

    # client_user_2 wants only their own entities (private or public)
    data = assert_request(
        client_user_2.get,
        url=route,
        params={"authorized_project_id": UNRELATED_PROJECT_ID},
    ).json()["data"]
    assert len(data) == 2
    assert {row["id"] for row in data} == {public_u2_0["id"], private_u2_0["id"]}

    # client_user_1 wants only their own public entities
    data = assert_request(
        client_user_1.get,
        url=route,
        params={"authorized_public": True, "authorized_project_id": PROJECT_ID},
    ).json()["data"]
    assert len(data) == 1
    assert {row["id"] for row in data} == {public_u1_0["id"]}

    # client_user_1 wants only their own private entities
    data = assert_request(
        client_user_1.get,
        url=route,
        params={"authorized_public": False, "authorized_project_id": PROJECT_ID},
    ).json()["data"]
    assert len(data) == 2
    assert {row["id"] for row in data} == {private_u1_0["id"], private_u1_1["id"]}


def check_brain_region_filter(route, client, db, brain_region_hierarchy_id, create_model_function):
    db_hierarchy = db.get(BrainRegionHierarchy, brain_region_hierarchy_id)

    brain_region_ids = [
        create_brain_region(
            db,
            brain_region_hierarchy_id,
            annotation_value=i,
            name=f"region-{i}",
            created_by_id=db_hierarchy.created_by_id,
        ).id
        for i in range(2)
    ]

    _ = [
        add_db(db, create_model_function(db, name=f"name-{i}", brain_region_id=brain_region_id))
        for i, brain_region_id in enumerate(brain_region_ids)
    ]
    data = assert_request(
        client.get,
        url=route,
        params={"brain_region__name": "region-0", "with_facets": True},
    ).json()
    assert len(data["data"]) == 1
    assert data["facets"]["brain_region"] == [
        {"id": ANY, "label": "region-0", "count": 1, "type": "brain_region"},
    ]


def with_creation_fields(d):
    return d | {
        "creation_date": ANY,
        "update_date": ANY,
        "id": ANY,
    }


def add_brain_region_hierarchy(db, hierarchy, hierarchy_id):
    regions = []

    db_hierarchy = db.get(BrainRegionHierarchy, hierarchy_id)

    def recurse(i):
        children = []
        item = i | {"children": children}
        for child in i["children"]:
            children.append(child["id"])
            recurse(child)
        regions.append(item)

    recurse(hierarchy)

    ids = {None: None}
    for region in reversed(regions):
        row = BrainRegion(
            annotation_value=region["id"],
            acronym=region["acronym"],
            name=region["name"],
            color_hex_triplet=region["color_hex_triplet"],
            parent_structure_id=ids[region["parent_structure_id"]],
            hierarchy_id=hierarchy_id,
            created_by_id=db_hierarchy.created_by_id,
            updated_by_id=db_hierarchy.created_by_id,
            embedding=1536 * [0.1],
        )
        db_br = add_db(db, row)
        db.flush()
        ids[region["id"]] = db_br.id

    ret = {row.acronym: row for row in db.execute(sa.select(BrainRegion)).scalars()}
    return ret


def _entity_type_to_route(entity_type: EntityType) -> EntityRoute:
    return EntityRoute[entity_type.name]


def route(entity_type: EntityType) -> str:
    return f"/{_entity_type_to_route(entity_type)}"


def upload_entity_asset(
    client,
    entity_type: EntityType,
    entity_id: UUID,
    files: dict[str, tuple],
    label: str,
    expected_status: int | None = 201,
):
    """Attach a file to an entity

    files maps to: (filename, file (or bytes), content_type, headers)
    """
    assert label
    data = {"label": label}
    response = client.post(f"{route(entity_type)}/{entity_id}/assets", files=files, data=data)
    if expected_status:
        assert response.status_code == expected_status
    return response


def create_person(
    db,
    *,
    pref_label: str,
    given_name: str | None = None,
    family_name: str | None = None,
    sub_id: str | None = None,
    created_by_id: uuid.UUID | None = None,
):
    agent_id = create_uuid()

    row = Person(
        id=agent_id,
        given_name=given_name,
        family_name=family_name,
        pref_label=pref_label,
        sub_id=sub_id,
        created_by_id=created_by_id or agent_id,
        updated_by_id=created_by_id or agent_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def check_creation_fields(data: dict):
    assert data["creation_date"] == ANY
    assert data["update_date"] == ANY
    assert data["created_by"]["id"] == ANY
    assert data["updated_by"]["id"] == ANY


def add_contribution(db, entity_id, agent_id, role_id, created_by_id):
    return add_db(
        db,
        Contribution(
            agent_id=agent_id,
            role_id=role_id,
            entity_id=entity_id,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        ),
    )


def count_db_class(db, db_class):
    return db.execute(sa.select(sa.func.count(db_class.id))).scalar()


def delete_entity_contributions(client_admin, entity_route, entity_id):
    data = assert_request(
        client_admin.get,
        url=f"{entity_route}/{entity_id}",
    ).json()

    for contribution in data["contributions"]:
        contribution_id = contribution["id"]
        assert_request(
            client_admin.delete,
            url=f"/admin/contribution/{contribution_id}",
        ).json()


def delete_entity_assets(client_admin, entity_route, entity_id):
    data = assert_request(
        client_admin.get,
        url=f"{entity_route}/{entity_id}",
    ).json()

    for json_asset in data["assets"]:
        asset_id = json_asset["id"]
        assert_request(
            client_admin.delete,
            url=f"/admin{entity_route}/{entity_id}/assets/{asset_id}",
        ).json()


def delete_entity_classifications(client, client_admin, entity_id):
    mtype_classifications = assert_request(
        client.get, url="/mtype-classification", params={"entity_id": str(entity_id)}
    ).json()["data"]

    if mtype_classifications:
        for classification in mtype_classifications:
            classification_id = classification["id"]
            assert_request(
                client_admin.delete,
                url=f"/admin/mtype-classification/{classification_id}",
            )

    etype_classifications = assert_request(
        client.get, url="/etype-classification", params={"entity_id": str(entity_id)}
    ).json()["data"]

    if etype_classifications:
        for classification in etype_classifications:
            classification_id = classification["id"]
            assert_request(
                client_admin.delete,
                url=f"/admin/etype-classification/{classification_id}",
            )


def check_sort_by_field(items, field_name):
    assert all(items[i][field_name] < items[i + 1][field_name] for i in range(len(items) - 1)), (
        f"Items unsorted by {field_name}"
    )


def create_subject_ids(db, *, created_by_id, n):
    strain_ids = []
    species_ids = []
    subject_ids = []

    for i in range(n):
        species_id = str(
            add_db(
                db,
                Species(
                    name=f"TestSpecies{i}",
                    taxonomy_id=f"{i}",
                    created_by_id=created_by_id,
                    updated_by_id=created_by_id,
                    embedding=[0.1] * 1536,  # Mocked embedding
                ),
            ).id
        )
        strain_id = str(
            add_db(
                db,
                Strain(
                    name=f"TestStrain{i}",
                    taxonomy_id=f"{i + 2}",
                    species_id=species_id,
                    created_by_id=created_by_id,
                    updated_by_id=created_by_id,
                    embedding=[0.1] * 1536,  # Mocked embedding
                ),
            ).id
        )
        subject_id = str(
            add_db(
                db,
                Subject(
                    name=f"test-subject-{i}",
                    description=f"test-description-{i}",
                    species_id=species_id,
                    strain_id=strain_id,
                    age_value=timedelta(days=14),
                    age_period="postnatal",
                    sex="female",
                    weight=1.5,
                    authorized_public=False,
                    authorized_project_id=PROJECT_ID,
                    created_by_id=str(created_by_id),
                    updated_by_id=str(created_by_id),
                ),
            ).id
        )
        strain_ids.append(strain_id)
        species_ids.append(species_id)
        subject_ids.append(subject_id)

    return subject_ids, species_ids, strain_ids


def check_global_read_one(
    *,
    route: str,
    admin_route: str,
    clients: ClientProxies,
    json_data: dict,
    validator: Callable[[dict, dict], None],
):
    model_id = assert_request(clients.admin.post, url=route, json=json_data).json()["id"]

    def _req(client, client_route):
        data = assert_request(client.get, url=f"{client_route}/{model_id}").json()
        validator(data, json_data)

    # user that created the resource can read it
    _req(clients.user_1, route)

    # but cannot use the admin endpoint
    data = assert_request(
        clients.user_1.get,
        url=f"{admin_route}/{model_id}",
        expected_status_code=403,
    ).json()
    assert data["message"] == "Service admin role required"

    # any other user can read it too because it is global
    _req(clients.user_2, route)

    # but cannot use the admin endpoint
    data = assert_request(
        clients.user_2.get,
        url=f"{admin_route}/{model_id}",
        expected_status_code=403,
    ).json()
    assert data["message"] == "Service admin role required"

    # service admins can read from both regular and admin routes
    _req(clients.admin, route)
    _req(clients.admin, admin_route)


def check_global_update_one(
    *,
    route: str,
    admin_route: str,
    clients: ClientProxies,
    json_data: dict,
    patch_payload: dict,
):
    def _patch_compare(method, url, patch_data):
        data = assert_request(method, url=url, json=patch_data).json()
        for key, value in patch_data.items():
            assert data[key] == value, f"Key: {key} Expected: {value} Actual: {data[key]}"

    data = assert_request(clients.admin.post, url=route, json=json_data).json()
    model_id = data["id"]

    old_values = {k: data[k] for k in patch_payload}

    # global resource update endpoint requires admin client
    data = assert_request(
        clients.user_1.patch,
        url=f"{route}/{model_id}",
        json=patch_payload,
        expected_status_code=403,
    ).json()
    assert data["message"] == "Service admin role required"

    # update using admin client and regular route
    _patch_compare(clients.admin.patch, f"{route}/{model_id}", patch_payload)

    # revert
    _patch_compare(clients.admin.patch, f"{route}/{model_id}", old_values)

    # global resource admin endpoint requires admin client
    data = assert_request(
        clients.user_1.patch,
        url=f"{admin_route}/{model_id}",
        json=patch_payload,
        expected_status_code=403,
    ).json()
    assert data["message"] == "Service admin role required"

    # update using admin client and admin route
    _patch_compare(clients.admin.patch, f"{admin_route}/{model_id}", patch_payload)

    # revert
    _patch_compare(clients.admin.patch, f"{admin_route}/{model_id}", old_values)


def check_entity_update_one(
    *,
    route: str,
    admin_route: str,
    clients: ClientProxies,
    json_data: dict,
    patch_payload: dict,
    optional_payload: dict | None,
):
    def _create(client, json_data):
        return assert_request(client, url=route, json=json_data).json()

    def _patch_compare(method, url, patch_data):
        data = assert_request(method, url=url, json=patch_data).json()
        for key, value in patch_data.items():
            assert data[key] == value, f"Key: {key} Expected: {value} Actual: {data[key]}"

    public_1_data = _create(clients.user_1.post, json_data | {"authorized_public": True})
    private_1_data = _create(clients.user_1.post, json_data | {"authorized_public": False})
    private_1_old_values = {k: private_1_data[k] for k in patch_payload}

    assert public_1_data["authorized_public"] is True
    assert private_1_data["authorized_public"] is False

    public_1_id = public_1_data["id"]
    private_1_id = private_1_data["id"]

    # user updates resource
    _patch_compare(clients.user_1.patch, f"{route}/{private_1_id}", patch_payload)

    # user restores resource
    _patch_compare(clients.user_1.patch, f"{route}/{private_1_id}", private_1_old_values)

    # Test setting and unsetting optional fields
    if optional_payload:
        _patch_compare(clients.user_1.patch, f"{route}/{private_1_id}", optional_payload)
        _patch_compare(
            clients.user_1.patch, f"{route}/{private_1_id}", dict.fromkeys(optional_payload)
        )

    # only admin client can hit admin endpoint
    data = assert_request(
        clients.user_1.patch,
        url=f"{admin_route}/{private_1_id}",
        json={},
        expected_status_code=403,
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    _patch_compare(clients.admin.patch, f"{admin_route}/{private_1_id}", patch_payload)

    # admin is treated as regular user for regular route (no authorized project ids)
    data = assert_request(
        clients.admin.patch,
        url=f"{route}/{private_1_id}",
        json={},
        expected_status_code=404,
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"

    # user should not be allowed to update a public resource
    data = assert_request(
        clients.user_1.patch,
        url=f"{route}/{public_1_id}",
        json={},
        expected_status_code=404,
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"

    # admin has no such restrictions
    _patch_compare(
        clients.admin.patch, f"{admin_route}/{public_1_id}", {"authorized_public": False}
    )


def _get_entity(db, entity_id) -> Entity:
    q = sa.select(Entity).where(Entity.id == entity_id)
    return db.execute(q).scalars().one()


def check_activity_create_one__unauthorized_entities(
    db,
    route,
    client_user_1,
    json_data,
    u1_private_entity_id,
    u2_private_entity_id,
    u2_public_entity_id,
):
    """Do not allow associations with entities that are not authorized to the user."""

    # sanity check to ensure that authorized_project_id and authorized_public are consistent
    e1 = _get_entity(db, entity_id=u1_private_entity_id)
    e2 = _get_entity(db, entity_id=u2_private_entity_id)
    e3 = _get_entity(db, entity_id=u2_public_entity_id)
    assert e1.authorized_public is False
    assert e2.authorized_public is False
    assert e3.authorized_public is True
    assert e1.authorized_project_id != e2.authorized_project_id
    assert e2.authorized_project_id == e3.authorized_project_id

    # user1 is forbidden to create Usage association with entity created by user2
    unauthorized_used = json_data | {
        "used_ids": [str(u2_private_entity_id)],
        "generated_ids": [str(u1_private_entity_id)],
    }
    assert_request(client_user_1.post, url=route, json=unauthorized_used, expected_status_code=404)

    # user1 is forbidden to create Generation association with entity created by user2
    unauthorized_used = json_data | {
        "used_ids": [str(u1_private_entity_id)],
        "generated_ids": [str(u2_private_entity_id)],
    }
    assert_request(client_user_1.post, url=route, json=unauthorized_used, expected_status_code=404)

    # user1 is forbidden to create both associations with entities created by user 2
    unauthorized_used = json_data | {
        "used_ids": [str(u2_private_entity_id)],
        "generated_ids": [str(u2_private_entity_id)],
    }
    assert_request(client_user_1.post, url=route, json=unauthorized_used, expected_status_code=404)

    # user 1 is allowed to create Usage with public entity created by user2
    authorized_used = json_data | {
        "used_ids": [str(u2_public_entity_id)],
        "generated_ids": [str(u1_private_entity_id)],
    }
    assert_request(client_user_1.post, url=route, json=authorized_used, expected_status_code=200)

    # user 1 is allowed to create Generation with public entity created by user2
    authorized_used = json_data | {
        "used_ids": [str(u1_private_entity_id)],
        "generated_ids": [str(u2_public_entity_id)],
    }
    assert_request(client_user_1.post, url=route, json=authorized_used, expected_status_code=200)

    # user 1 is allowed to create both with public entity created by user2
    authorized_used = json_data | {
        "used_ids": [str(u2_public_entity_id)],
        "generated_ids": [str(u2_public_entity_id)],
    }
    assert_request(client_user_1.post, url=route, json=authorized_used, expected_status_code=200)


def check_activity_update_one(
    client, client_admin, route, admin_route, used_id, generated_id, constructor_func
):
    entity_id = constructor_func(
        used_ids=[str(used_id)],
        generated_ids=[],
    )

    end_time = datetime.now(UTC)

    update_json = {
        "end_time": str(end_time),
        "generated_ids": [str(generated_id)],
    }

    data = assert_request(client.patch, url=f"{route}/{entity_id}", json=update_json).json()
    assert DateTimeAdapter.validate_python(data["end_time"]) == end_time
    assert len(data["generated"]) == 1
    assert data["generated"][0]["id"] == str(generated_id)

    # only admin client can hit admin endpoint
    data = assert_request(
        client.patch,
        url=f"{admin_route}/{entity_id}",
        json=update_json,
        expected_status_code=403,
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    entity_id = constructor_func(
        used_ids=[str(used_id)],
        generated_ids=[],
    )

    data = assert_request(
        client_admin.patch,
        url=f"{admin_route}/{entity_id}",
        json=update_json,
    ).json()

    assert DateTimeAdapter.validate_python(data["end_time"]) == end_time
    assert len(data["generated"]) == 1
    assert data["generated"][0]["id"] == str(generated_id)

    # admin is treated as regular user for regular route (no project context)
    data = assert_request(
        client_admin.patch,
        url=f"{route}/{entity_id}",
        json=update_json,
        expected_status_code=403,
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"


def check_activity_update_one__fail_if_generated_ids_unauthorized(
    db,
    route,
    client_user_1,
    json_data,
    u1_private_entity_id,
    u2_private_entity_id,
):
    """Test that it is not allowed to update generated_ids with unauthorized entities."""
    # sanity check to ensure that authorized_project_id and authorized_public are consistent
    e1 = _get_entity(db, entity_id=u1_private_entity_id)
    e2 = _get_entity(db, entity_id=u2_private_entity_id)
    assert e1.authorized_public is False
    assert e2.authorized_public is False
    assert e1.authorized_project_id != e2.authorized_project_id

    json_data |= {
        "used_ids": [str(u1_private_entity_id)],
        "generated_ids": [],
    }

    data = assert_request(client_user_1.post, url=route, json=json_data).json()

    update_json = {
        "generated_ids": [str(u2_private_entity_id)],
    }
    data = assert_request(
        client_user_1.patch, url=f"{route}/{data['id']}", json=update_json, expected_status_code=404
    ).json()
    assert data["details"] == f"Cannot access entities {u2_private_entity_id}"


def check_activity_update_one__fail_if_generated_ids_exists(
    client, route, entity_id_1, entity_id_2, constructor_func
):
    gen1 = constructor_func(
        used_ids=[str(entity_id_1)],
        generated_ids=[str(entity_id_2)],
    )
    update_json = {
        "generated_ids": [str(entity_id_1)],
    }
    data = assert_request(
        client.patch, url=f"{route}/{gen1}", json=update_json, expected_status_code=404
    ).json()
    assert data["details"] == "It is forbidden to update generated_ids if they exist."
