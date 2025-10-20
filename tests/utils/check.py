import re
import uuid

from tests.utils import PROJECT_ID, ClientProxy, assert_request


def check_auth_triggers(
    route,
    *,
    client_user_1: ClientProxy,
    json_data: dict,
    link_key: str,
    linked_private_u1_id: uuid.UUID | str,
    linked_public_u1_id: uuid.UUID | str,
    linked_private_u2_id: uuid.UUID | str,
    linked_public_u2_id: uuid.UUID | str,
):
    """Check the authorization triggers when creating an entity having a linked entity.

    The following table summarizes what are the expected permitted links
    between the main entity and the linked entity.

    main/linked | private_u1 | private_u2 | public_u1 | public_u2
    ------------|------------|------------|-----------|-----------
    private_u1  | y          | n          | y         | y
    public_u1   | n          | n          | y         | y

    Args:
        client_user_1: user_1 client.
        json_data: json data that will be sent to the create endpoint.
        link_key: name of the key that contains the reference to the linked entity.
        linked_private_u1_id: id of an existing private entity belonging to user_1.
        linked_public_u1_id: id of an existing public entity belonging to user_1.
        linked_private_u2_id: id of an existing private entity belonging to user_2.
        linked_public_u2_id: id of an existing public entity belonging to user_2.
    """

    err_template = (
        r"One of the entities referenced by .* is not public or not owned by the user .*"
        r"unauthorized private reference: .*\.{}"
    )

    # main_private_u1, linked_private_u1
    result = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"authorized_public": False, link_key: str(linked_private_u1_id)},
        expected_status_code=200,
    ).json()
    assert result["authorized_public"] is False
    assert result["authorized_project_id"] == PROJECT_ID

    # main_private_u1, linked_private_u2
    result = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"authorized_public": False, link_key: str(linked_private_u2_id)},
        expected_status_code=403,
    ).json()
    assert re.match(err_template.format(link_key), result["message"])

    # main_private_u1, linked_public_u1
    result = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"authorized_public": False, link_key: str(linked_public_u1_id)},
        expected_status_code=200,
    ).json()
    assert result["authorized_public"] is False
    assert result["authorized_project_id"] == PROJECT_ID

    # main_private_u1, linked_public_u2
    result = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"authorized_public": False, link_key: str(linked_public_u2_id)},
        expected_status_code=200,
    ).json()
    assert result["authorized_public"] is False
    assert result["authorized_project_id"] == PROJECT_ID

    # main_public_u1, linked_private_u1
    result = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"authorized_public": True, link_key: str(linked_private_u1_id)},
        expected_status_code=403,
    ).json()
    assert re.match(err_template.format(link_key), result["message"])

    # main_public_u1, linked_private_u2
    result = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"authorized_public": True, link_key: str(linked_private_u2_id)},
        expected_status_code=403,
    ).json()
    assert re.match(err_template.format(link_key), result["message"])

    # main_public_u1, linked_public_u1
    result = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"authorized_public": True, link_key: str(linked_public_u1_id)},
        expected_status_code=200,
    ).json()
    assert result["authorized_public"] is True
    assert result["authorized_project_id"] == PROJECT_ID

    # main_public_u1, linked_public_u2
    result = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"authorized_public": True, link_key: str(linked_public_u2_id)},
        expected_status_code=200,
    ).json()
    assert result["authorized_public"] is True
    assert result["authorized_project_id"] == PROJECT_ID
