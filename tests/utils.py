import functools
import uuid
from pathlib import Path
from unittest.mock import ANY

import sqlalchemy as sa
from httpx import Headers
from starlette.testclient import TestClient

from app.db.model import (
    BrainRegion,
    BrainRegionHierarchy,
    ElectricalCellRecording,
    ElectricalRecordingStimulus,
    MTypeClass,
    MTypeClassification,
    ReconstructionMorphology,
)
from app.db.types import EntityType

TEST_DATA_DIR = Path(__file__).parent / "data"

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
    ReconstructionMorphology: "/reconstruction-morphology",
    ElectricalCellRecording: "/electrical-cell-recording",
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


def create_reconstruction_morphology_id(
    client,
    species_id,
    strain_id,
    brain_region_id,
    authorized_public,
    name="Test Morphology Name",
    description="Test Morphology Description",
):
    response = client.post(
        ROUTES[ReconstructionMorphology],
        json={
            "name": name,
            "description": description,
            "brain_region_id": str(brain_region_id),
            "species_id": str(species_id) if species_id else None,
            "strain_id": str(strain_id) if strain_id else None,
            "location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": ["Test Legacy ID"],
            "authorized_public": authorized_public,
        },
    )

    assert response.status_code == 200
    return response.json()["id"]


def add_db(db, row):
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def add_all_db(db, rows):
    db.add_all(rows)
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


def create_hiearchy_name(db, name: str):
    row = BrainRegionHierarchy(name=name)
    return add_db(db, row)


def create_brain_region(
    db,
    hierarchy_id,
    annotation_value: int,
    name: str,
    parent_id: uuid.UUID | None = None,
):
    row = BrainRegion(
        annotation_value=annotation_value,
        acronym=f"acronym{annotation_value}",
        name=name,
        color_hex_triplet="FF0000",
        parent_structure_id=parent_id,
        hierarchy_id=hierarchy_id,
    )
    return add_db(db, row)


def create_mtype(db, pref_label: str, alt_label=None, definition=None):
    return add_db(
        db,
        MTypeClass(
            pref_label=pref_label,
            alt_label=alt_label or pref_label,
            definition=definition or "",
        ),
    )


def attach_mtype(db, entity_id, mtype_id):
    return add_db(db, MTypeClassification(entity_id=str(entity_id), mtype_class_id=str(mtype_id)))


def create_electrical_recording_stimulus_id(db, recording_id):
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

    # add two protocols that refer to it
    create_electrical_recording_stimulus_id(db, trace_id)
    create_electrical_recording_stimulus_id(db, trace_id)

    filepath = tmp_path / "trace.nwb"
    filepath.write_bytes(b"trace")

    # add an asset too
    create_asset_file(
        client=client,
        entity_type="electrical_cell_recording",
        entity_id=trace_id,
        file_name="my-trace.nwb",
        file_obj=filepath.read_bytes(),
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
    response = assert_request(
        client_user_1.post,
        url=route,
        json=json_data
        | {
            "name": "Public Entity",
            "authorized_public": True,
        },
    )
    public_morph = response.json()

    inaccessible_obj = assert_request(
        client_user_2.post,
        url=route,
        json=json_data | {"name": "inaccessible morphology 1"},
    )
    inaccessible_obj = inaccessible_obj.json()

    private_obj0 = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"name": "private morphology 0"},
    )
    private_obj0 = private_obj0.json()

    private_obj1 = assert_request(
        client_user_1.post,
        url=route,
        json=json_data
        | {
            "name": "private morphology 1",
        },
    )
    private_obj1 = private_obj1.json()

    # only return results that matches the desired project, and public ones
    response = assert_request(
        client_user_1.get,
        url=route,
    )
    data = response.json()["data"]

    ids = {row["id"] for row in data}
    expected = {
        public_morph["id"],
        private_obj0["id"],
        private_obj1["id"],
    }
    assert ids == expected, (
        "Failed to fetch project-specific and public ids.\n"
        f"Expected: {sorted(expected)}\n"
        f"Actual  : {sorted(ids)}"
    )

    assert_request(
        client_user_1.get,
        url=f"{route}/{inaccessible_obj['id']}",
        expected_status_code=404,
    )

    # only returns public results
    response = assert_request(
        client_no_project.get,
        url=route,
    )
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == public_morph["id"]


def create_asset_file(client, entity_type, entity_id, file_name, file_obj):
    route = EntityType[entity_type].replace("_", "-")
    files = {
        # (filename, file (or bytes), content_type, headers)
        "file": (str(file_name), file_obj, "text/plain")
    }
    assert_request(
        client.post,
        url=f"{route}/{entity_id}/assets",
        files=files,
        expected_status_code=201,
    )


def check_brain_region_filter(route, client, db, brain_region_hierarchy_id, create_model_function):
    brain_region_ids = [
        create_brain_region(
            db, brain_region_hierarchy_id, annotation_value=i, name=f"region-{i}"
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
        )
        db_br = add_db(db, row)
        db.flush()
        ids[region["id"]] = db_br.id

    ret = {row.acronym: row for row in db.execute(sa.select(BrainRegion)).scalars()}
    return ret
