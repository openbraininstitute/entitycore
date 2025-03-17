import pytest
import itertools as it

from .utils import BEARER_TOKEN, PROJECT_HEADERS, add_db, create_reconstruction_morphology_id

ROUTE = "/emodel"


@pytest.mark.usefixtures("skip_project_check")
def test_create_emodel(client, species_id, strain_id, brain_region_id, exemplar_morphology_id):
    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": "Test EModel Description",
            "name": "Test EModel Name",
            "legacy_id": "Test Legacy ID",
            "iteration": "test iteration",
            "score": -1,
            "seed": -1,
            "exemplar_morphology_id": exemplar_morphology_id,
        },
    )
    assert response.status_code == 200, f"Failed to create emodel: {response.text}"
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id, f"Failed to get id for emodel: {data}"
    assert data["species"]["id"] == species_id, f"Failed to get species_id for emodel: {data}"
    assert data["strain"]["id"] == strain_id, f"Failed to get strain_id for emodel: {data}"

    response = client.get(ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 200, f"Failed to get emodels: {response.text}"


@pytest.mark.usefixtures("skip_project_check")
def test_missing(client):
    response = client.get(f"{ROUTE}/42424242", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notanumber", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 422


@pytest.mark.usefixtures("skip_project_check")
def test_query_emodel(client, create_emodel_ids):
    count = 11
    create_emodel_ids(count)

    response = client.get(
        ROUTE,
        params={"page_size": 10},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert response.status_code == 200
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 10

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"page_size": 100},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 11


@pytest.mark.usefixtures("skip_project_check")
def test_emodels_sorted(client, create_emodel_ids):
    count = 11
    create_emodel_ids(count)

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "+creation_date", "page_size": 100},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count
    assert all(
        elem["creation_date"] > prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = client.get(
        ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS, params={"order_by": "-creation_date"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert all(
        elem["creation_date"] < prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "+creation_date", "page": 1, "page_size": 3},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3
    assert [row["id"] for row in data] == [2, 3, 4]


@pytest.mark.usefixtures("skip_project_check")
def test_facets(client, create_faceted_emodel_ids):
    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"with_facets": True},
    )
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]

    assert facets == {
        "mtype": [],
        "etype": [],
        "species": [
            {"id": 1, "label": "TestSpecies0", "count": 4, "type": "species"},
            {"id": 2, "label": "TestSpecies1", "count": 4, "type": "species"},
        ],
        "contribution": [],
        "brain_region": [
            {"id": 0, "label": "region0", "count": 4, "type": "brain_region"},
            {"id": 1, "label": "region1", "count": 4, "type": "brain_region"},
        ],
        "exemplar_morphology": [
            {"id": 1, "label": "Test Morphology Name", "count": 4, "type": "exemplar_morphology"},
            {"id": 2, "label": "Test Morphology Name", "count": 4, "type": "exemplar_morphology"},
        ],
    }


# @pytest.mark.usefixtures("skip_project_check")
# def test_query_reconstruction_morphology(db, client, brain_region_id):


#     response = client.get(
#         ROUTE,
#         headers=BEARER_TOKEN | PROJECT_HEADERS,
#         params={"with_facets": True},
#     )
#     assert response.status_code == 200
#     data = response.json()

#     assert "facets" in data
#     facets = data["facets"]
#     assert facets == {
#         "contribution": [],
#         "mtype": [],
#         "species": [
#             {"id": 1, "label": "TestSpecies1", "count": 6, "type": "species"},
#             {"id": 2, "label": "TestSpecies2", "count": 5, "type": "species"},
#         ],
#         "strain": [
#             {"id": 1, "label": "TestStrain1", "count": 6, "type": "strain"},
#             {"id": 2, "label": "TestStrain2", "count": 5, "type": "strain"},
#         ],
#     }

#     response = client.get(
#         ROUTE,
#         headers=BEARER_TOKEN | PROJECT_HEADERS,
#         params={"search": "Test", "with_facets": True},
#     )
#     assert response.status_code == 200
#     data = response.json()

#     assert "facets" in data
#     facets = data["facets"]
#     assert facets == {
#         "contribution": [],
#         "mtype": [],
#         "species": [
#             {"id": 1, "label": "TestSpecies1", "count": 6, "type": "species"},
#             {"id": 2, "label": "TestSpecies2", "count": 5, "type": "species"},
#         ],
#         "strain": [
#             {"id": 1, "label": "TestStrain1", "count": 6, "type": "strain"},
#             {"id": 2, "label": "TestStrain2", "count": 5, "type": "strain"},
#         ],
#     }

#     response = client.get(
#         ROUTE,
#         headers=BEARER_TOKEN | PROJECT_HEADERS,
#         params={"species__name": "TestSpecies1", "with_facets": True},
#     )
#     assert response.status_code == 200
#     data = response.json()
#     assert len(data["data"]) == 6

#     assert "facets" in data
#     facets = data["facets"]
#     assert facets == {
#         "contribution": [],
#         "mtype": [],
#         "species": [{"id": 1, "label": "TestSpecies1", "count": 6, "type": "species"}],
#         "strain": [{"id": 1, "label": "TestStrain1", "count": 6, "type": "strain"}],
#     }


# @pytest.mark.usefixtures("skip_project_check")
# def test_query_reconstruction_morphology_species_join(db, client, brain_region_id):
#     """Make sure not to join all the species w/ their strains while doing query"""
#     species0 = add_db(db, Species(name="TestSpecies0", taxonomy_id="1"))
#     strain0 = add_db(db, Strain(name="Strain0", taxonomy_id="strain0", species_id=species0.id))
#     add_db(db, Strain(name="Strain1", taxonomy_id="strain1", species_id=species0.id))

#     add_db(
#         db,
#         ReconstructionMorphology(
#             brain_region_id=brain_region_id,
#             species_id=species0.id,
#             strain_id=strain0.id,
#             description="description",
#             name="morph00",
#             location=None,
#             legacy_id="Test Legacy ID",
#             license_id=None,
#             authorized_project_id=PROJECT_HEADERS["project-id"],
#         ),
#     )

#     response = client.get(
#         ROUTE,
#         headers=BEARER_TOKEN | PROJECT_HEADERS,
#         params={"with_facets": True},
#     )
#     data = response.json()
#     assert len(data["data"]) == data["pagination"]["total_items"]
#     assert "facets" in data
#     assert data["facets"] == {
#         "contribution": [],
#         "mtype": [],
#         "species": [{"id": 1, "label": "TestSpecies0", "count": 1, "type": "species"}],
#         "strain": [{"id": 1, "label": "Strain0", "count": 1, "type": "strain"}],
#     }


# @pytest.mark.usefixtures("skip_project_check")
# def test_authorization(client, species_id, strain_id, license_id, brain_region_id):
#     morph_json = {
#         "location": {"x": 10, "y": 20, "z": 30},
#         "brain_region_id": brain_region_id,
#         "description": "morph description",
#         "legacy_id": "Test Legacy ID",
#         "license_id": license_id,
#         "name": "Test Morphology Name",
#         "species_id": species_id,
#         "strain_id": strain_id,
#     }

#     public_morph = client.post(
#         ROUTE,
#         headers=BEARER_TOKEN | PROJECT_HEADERS,
#         json=morph_json
#         | {
#             "name": "public morphology",
#             "authorized_public": True,
#         },
#     )
#     assert public_morph.status_code == 200
#     public_morph = public_morph.json()

#     inaccessible_obj = client.post(
#         ROUTE,
#         headers=BEARER_TOKEN
#         | {
#             "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
#             "project-id": "42424242-4242-4000-9000-424242424242",
#         },
#         json=morph_json | {"name": "unaccessable morphology 1"},
#     )
#     assert inaccessible_obj.status_code == 200
#     inaccessible_obj = inaccessible_obj.json()

#     private_morph0 = client.post(
#         ROUTE,
#         headers=BEARER_TOKEN | PROJECT_HEADERS,
#         json=morph_json | {"name": "private morphology 0"},
#     )
#     assert private_morph0.status_code == 200
#     private_morph0 = private_morph0.json()

#     private_morph1 = client.post(
#         ROUTE,
#         headers=BEARER_TOKEN | PROJECT_HEADERS,
#         json=morph_json
#         | {
#             "name": "private morphology 1",
#         },
#     )
#     assert private_morph1.status_code == 200
#     private_morph1 = private_morph1.json()

#     # only return results that matches the desired project, and public ones
#     response = client.get(ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
#     data = response.json()["data"]
#     assert len(data) == 3

#     ids = {row["id"] for row in data}
#     assert ids == {
#         public_morph["id"],
#         private_morph0["id"],
#         private_morph1["id"],
#     }

#     response = client.get(
#         f"{ROUTE}/{inaccessible_obj['id']}", headers=BEARER_TOKEN | PROJECT_HEADERS
#     )
#     assert response.status_code == 404


# @pytest.mark.usefixtures("skip_project_check")
# def test_pagination(db, client, brain_region_id):
#     species0 = add_db(db, Species(name="TestSpecies0", taxonomy_id="0"))
#     species1 = add_db(db, Species(name="TestSpecies1", taxonomy_id="1"))
#     strain0 = add_db(db, Strain(name="Strain0", taxonomy_id="strain0", species_id=species0.id))
#     strain1 = add_db(db, Strain(name="Strain1", taxonomy_id="strain1", species_id=species1.id))

#     total_items = 29
#     for i, (species, strain) in zip(
#         range(total_items), it.cycle(((species0, None), (species0, strain0), (species1, strain1)))
#     ):
#         create_reconstruction_morphology_id(
#             client,
#             species.id,
#             strain.id if strain else None,
#             brain_region_id,
#             headers=BEARER_TOKEN | PROJECT_HEADERS,
#             name=f"TestMorphologyName{i}",
#             authorized_public=False,
#         )

#     response = client.get(
#         ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS, params={"page_size": total_items + 1}
#     )

#     assert response.status_code == 200
#     assert len(response.json()["data"]) == total_items

#     for i in range(1, total_items + 10, 2):
#         response = client.get(
#             ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS, params={"page_size": i}
#         )

#         assert response.status_code == 200
#         data = response.json()["data"]
#         expected_items = min(i, total_items)
#         assert len(data) == expected_items
#         names = [int(d["name"].removeprefix("TestMorphologyName")) for d in data]
#         assert list(names) == list(range(total_items - 1, total_items - expected_items - 1, -1))

#     items = []
#     for i in range(1, total_items + 1):
#         response = client.get(
#             ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS, params={"page": i, "page_size": 1}
#         )

#         assert response.status_code == 200
#         data = response.json()["data"]
#         assert len(data) == 1
#         items.append(data[0])

#     assert len(items) == total_items
#     names = [int(d["name"].removeprefix("TestMorphologyName")) for d in items]
#     assert list(reversed(names)) == list(range(total_items))
