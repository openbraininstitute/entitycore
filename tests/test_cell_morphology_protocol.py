import pytest

from app.db.model import (
    CellMorphologyProtocolDesign,
    ComputationallySynthesizedCellMorphologyProtocol,
    DigitalReconstructionCellMorphologyProtocol,
    ModifiedReconstructionCellMorphologyProtocol,
    PlaceholderCellMorphologyProtocol,
)
from app.db.types import (
    CellMorphologyGenerationType,
    ModifiedMorphologyMethodType,
    SlicingDirectionType,
)
from app.schemas.cell_morphology_protocol import (
    ComputationallySynthesizedCellMorphologyProtocolCreate,
    DigitalReconstructionCellMorphologyProtocolCreate,
    ModifiedReconstructionCellMorphologyProtocolCreate,
    PlaceholderCellMorphologyProtocolCreate,
)

from .utils import (
    PROJECT_ID,
    add_all_db,
    assert_request,
    check_authorization,
    check_missing,
    check_pagination,
)

ROUTE = "/cell-morphology-protocol"


@pytest.fixture
def json_data_digital_reconstruction():
    return DigitalReconstructionCellMorphologyProtocolCreate.model_validate(
        {
            "generation_type": CellMorphologyGenerationType.digital_reconstruction,
            "protocol_design": CellMorphologyProtocolDesign.cell_patch,
            "protocol_document": "https://example.com",
            "slicing_direction": SlicingDirectionType.horizontal,
            "slicing_thickness": 200,
        }
    ).model_dump(mode="json")


@pytest.fixture
def json_data_modified_reconstruction():
    return ModifiedReconstructionCellMorphologyProtocolCreate.model_validate(
        {
            "generation_type": CellMorphologyGenerationType.modified_reconstruction,
            "protocol_design": CellMorphologyProtocolDesign.fluorophore,
            "method_type": ModifiedMorphologyMethodType.cloned,
        }
    ).model_dump(mode="json")


@pytest.fixture
def json_data_computationally_synthesized():
    return ComputationallySynthesizedCellMorphologyProtocolCreate.model_validate(
        {
            "generation_type": CellMorphologyGenerationType.computationally_synthesized,
            "protocol_design": CellMorphologyProtocolDesign.electron_microscopy,
            "method_type": "free-text",
        }
    ).model_dump(mode="json")


@pytest.fixture
def json_data_placeholder():
    return PlaceholderCellMorphologyProtocolCreate.model_validate(
        {
            "generation_type": CellMorphologyGenerationType.placeholder,
        }
    ).model_dump(mode="json")


@pytest.fixture
def json_data(json_data_digital_reconstruction):
    # to be used when testing one type is enough
    return json_data_digital_reconstruction


def _assert_read_response(actual, expected):
    ignored_keys = {
        "authorized_project_id",
        "creation_date",
        "update_date",
        "created_by",
        "updated_by",
        "id",
    }
    assert ignored_keys.issubset(actual)
    actual = {k: v for k, v in actual.items() if k not in ignored_keys}
    assert actual == expected


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(create_id):
    return create_id()


@pytest.mark.parametrize(
    "json_data_fixture",
    [
        "json_data_digital_reconstruction",
        "json_data_modified_reconstruction",
        "json_data_computationally_synthesized",
        "json_data_placeholder",
    ],
)
def test_create_one(request, client, json_data_fixture):
    json_data = request.getfixturevalue(json_data_fixture)
    expected = json_data.copy()
    # remove `type` from the request to ensure that's not required
    del json_data["type"]
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, expected)


def test_read_one(client, model_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()
    assert len(data["data"]) == 1
    _assert_read_response(data["data"][0], json_data)


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(
    client_user_1,
    client_user_2,
    client_no_project,
    json_data,
):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(
    db,
    person_id,
    json_data_digital_reconstruction,
    json_data_modified_reconstruction,
    json_data_computationally_synthesized,
    json_data_placeholder,
):
    common_fields = {
        "created_by_id": person_id,
        "updated_by_id": person_id,
        "authorized_project_id": PROJECT_ID,
        "authorized_public": False,
    }
    rows = add_all_db(
        db,
        [
            DigitalReconstructionCellMorphologyProtocol(
                **common_fields | json_data_digital_reconstruction,
            ),
            ModifiedReconstructionCellMorphologyProtocol(
                **common_fields | json_data_modified_reconstruction,
            ),
            ComputationallySynthesizedCellMorphologyProtocol(
                **common_fields | json_data_computationally_synthesized,
            ),
            PlaceholderCellMorphologyProtocol(
                **common_fields | json_data_placeholder,
            ),
        ],
    )
    return rows


def test_filtering(client, models):
    data = assert_request(client.get, url=ROUTE).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get, url=ROUTE, params={"generation_type": "digital_reconstruction"}
    ).json()["data"]
    assert len(data) == 1
    assert data[0]["generation_type"] == "digital_reconstruction"

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"generation_type__in": ["digital_reconstruction", "modified_reconstruction"]},
    ).json()["data"]
    assert len(data) == 2
    assert {d["generation_type"] for d in data} == {
        "digital_reconstruction",
        "modified_reconstruction",
    }


def test_sorting(client, models):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({"order_by": ["creation_date"]})
    assert len(data) == len(models)
    assert [d["id"] for d in data] == [str(m.id) for m in models]

    data = req({"order_by": "-creation_date"})
    assert len(data) == len(models)
    assert [d["id"] for d in data] == [str(m.id) for m in models][::-1]
