from . import TEST_SBO_END_POINT, get_body


def test_sbo_reconstruction_morphology(client):
    response = client.post(
        TEST_SBO_END_POINT,
        json=get_body("sbo_count_reconstruction_morphology"),
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["hits"]["total"]["value"], int)
    assert data["hits"]["total"]["value"] > 10


def test_sbo_experimental_bouton_density(client):
    response = client.post(
        TEST_SBO_END_POINT, json=get_body("sbo_count_experimental_bouton_density")
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["hits"]["total"]["value"], int)
    assert data["hits"]["total"]["value"] > 5


def test_sbo_experimental_neuron_density(client):
    response = client.post(
        TEST_SBO_END_POINT, json=get_body("sbo_count_experimental_neuron_density")
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["hits"]["total"]["value"], int)
    assert data["hits"]["total"]["value"] > 10


def test_sbo_experimental_synapses_per_connection(client):
    response = client.post(
        TEST_SBO_END_POINT,
        json=get_body("sbo_count_experimental_synapses_per_connection"),
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["hits"]["total"]["value"], int)
    assert data["hits"]["total"]["value"] == 6


def test_sbo_experimental_trace(client):
    response = client.post(
        TEST_SBO_END_POINT, json=get_body("sbo_count_experimental_trace")
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["hits"]["total"]["value"], int)
    assert data["hits"]["total"]["value"] > 10
