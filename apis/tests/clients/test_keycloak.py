# from apis.clients.keycloak.factory import make_or_get_keycloack_admin


# def test_fetch_user_by_username(mocker):
#     client = make_or_get_keycloack_admin()
#     mock_response = {"username": "bob", "email": "bob@example.com"}
#     mocker.patch.object(client, "get_user_by_username", return_value=mock_response)

#     user = client.get_user_by_username("bob")
#     assert user["email"] == "bob@example.com"