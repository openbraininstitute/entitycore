from app.routers import types as test_module


def test_routes_exist(client):
    failed = []
    routes = sorted(
        list(test_module.EntityRoute)
        + list(test_module.GlobalRoute)
        + list(test_module.ActivityRoute)
    )
    for route in routes:
        resp = client.get(f"/{route}")
        if not resp.is_success:
            failed.append((route, resp.json()))
    assert not failed, failed
