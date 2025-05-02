ROUTE = "/brain-region"


def test_get_brain_region(client):
    response = client.get(ROUTE)
    assert response.status_code == 200
    assert len(response.text) > 4_500_000


hierarchy = {
    "id": 997,
    "acronym": "root",
    "name": "root",
    "color_hex_triplet": "FFFFFF",
    "parent_structure_id": null,
    "children": [
        {
            "id": 8,
            "acronym": "grey",
            "name": "Basic cell groups and regions",
            "color_hex_triplet": "BFDAE3",
            "parent_structure_id": 997,
            "children": [],
        },
        {
            "id": 42,
            "acronym": "blue",
            "name": "BlueRegion",
            "color_hex_triplet": "0000FF",
            "parent_structure_id": 997,
            "children": [
                {
                    "id": 64,
                    "acronym": "red",
                    "name": "RedRegion",
                    "color_hex_triplet": "FF0000",
                    "parent_structure_id": 42,
                    "children": [],
                }
            ],
        },
    ],
}


def _get_flat_regions(hierarchy):
    regions = []

    def recurse(i):
        children = []
        item = i | {"children": children}
        for child in i["children"]:
            children.append(child["id"])
            recurse(child)
        regions.append(item)

    return recurse(hierarchy)


def test_brain_region_id(client_admin, client):
    regions = _get_flat_regions(hierarchy)
    for region in regions:
        response = client_admin.post(
            ROUTE,
            json=region,
        )
        assert response.status_code == 200, f"Failed to create brain region: {response.text}"

    response = client.get(f"{ROUTE}/997")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 997
    assert data["name"] == "root"
    assert data["acronym"] == "root"
    assert data["children"] == [8, 42]

    response = client.get(ROUTE, params={"flat": True})
    assert response.status_code == 200
    data = response.json()
    assert data == [
        [997, "root", "root", [8, 42], 1],
        [8, "Basic cell groups and regions", "grey", [], 2],
        [42, "BlueRegion", "blue", [64], 2],
        [64, "RedRegion", "red", [], 3],
    ]
