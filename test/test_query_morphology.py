def test_query_reconstruction_morphology(client):
    def create_morphologies(client, nb_morph=3):
        response = client.post("/species/", json={"name": "Test Species", "taxonomy_id": "12345"})
        assert response.status_code == 200, f"Failed to create species: {response.text}"
        data = response.json()
        species_id = data["id"]
        response = client.post(
            "/strain/",
            json={
                "name": "Test Strain",
                "taxonomy_id": "Taxonomy ID",
                "species_id": species_id,
            },
        )
        assert response.status_code == 200, f"Failed to create strain: {response.text}"
        data = response.json()
        strain_id = data["id"]
        ontology_id = "Test Ontology ID"
        response = client.post(
            "/brain_region/", json={"name": "Test Brain Region", "ontology_id": ontology_id}
        )
        assert response.status_code == 200, f"Failed to create brain region: {response.text}"
        data = response.json()
        assert "id" in data, f"Failed to get id for brain region: {data}"
        brain_region_id = data["id"]
        response = client.post(
            "/license/",
            json={
                "name": "Test License",
                "description": "a license description",
                "label": "test label",
            },
        )
        assert response.status_code == 200
        data = response.json()
        license_id = data["id"]
        for i in range(nb_morph):
            morph_description = f"Test Morphology Description {i}"
            morph_name = f"Test Morphology Name {i}"
            response = client.post(
                "/reconstruction_morphology/",
                json={
                    "brain_region_id": brain_region_id,
                    "species_id": species_id,
                    "strain_id": strain_id,
                    "description": morph_description,
                    "name": morph_name,
                    "brain_location": {"x": 10, "y": 20, "z": 30},
                    "legacy_id": "Test Legacy ID",
                    "license_id": license_id,
                },
            )
            assert (
                response.status_code == 200
            ), f"Failed to create reconstruction morphology: {response.text}"
            import time

            time.sleep(1.1)

    create_morphologies(client)
    response = client.get("/reconstruction_morphology/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # response = client.get("/reconstruction_morphology/")
    response = client.get("/reconstruction_morphology/", params={"order_by": "+creation_date"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    prev_elem = None
    for elem in data:
        if prev_elem:
            print(elem["creation_date"], prev_elem["creation_date"])
            assert elem["creation_date"] > prev_elem["creation_date"]
        prev_elem = elem

    response = client.get("/reconstruction_morphology/", params={"order_by": "-creation_date"})
    assert response.status_code == 200
    data = response.json()
    prev_elem = None
    for elem in data:
        if prev_elem:
            print(elem["creation_date"], prev_elem["creation_date"])
            assert elem["creation_date"] < prev_elem["creation_date"]
        prev_elem = elem
