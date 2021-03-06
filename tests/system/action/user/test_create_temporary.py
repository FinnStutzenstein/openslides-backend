from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class UserCreateTemporaryActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/222", {"name": "name_shjeuazu"})
        response = self.request(
            "user.create_temporary", {"username": "test_Xcdfgee", "meeting_id": 222}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/2")
        assert model.get("username") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("is_physical_person") is True

    def test_create_all_fields(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_shjeuazu"},
                "group/1": {"meeting_id": 222},
                "user/7": {"meeting_id": 222},
            }
        )
        response = self.request(
            "user.create_temporary",
            {
                "username": "test_Xcdfgee",
                "meeting_id": 222,
                "title": "title",
                "first_name": "first_name",
                "last_name": "last_name",
                "is_active": True,
                "is_physical_person": False,
                "gender": "gender",
                "default_number": "number",
                "default_structure_level": "structure_level",
                "email": "email",
                "default_vote_weight": "1.000000",
                "is_present_in_meeting_ids": [222],
                "default_password": "password",
                "group_ids": [1],
                "vote_delegations_from_ids": [7],
                "comment": "comment<iframe></iframe>",
                "number": "number",
                "structure_level": "level",
                "about_me": "<p>about</p><iframe></iframe>",
                "vote_weight": "1.000000",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/8")
        assert model.get("username") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("title") == "title"
        assert model.get("first_name") == "first_name"
        assert model.get("last_name") == "last_name"
        assert model.get("is_active") is True
        assert model.get("is_physical_person") is False
        assert model.get("gender") == "gender"
        assert model.get("default_number") == "number"
        assert model.get("default_structure_level") == "structure_level"
        assert model.get("email") == "email"
        assert model.get("default_vote_weight") == "1.000000"
        assert model.get("is_present_in_meeting_ids") == [222]
        assert model.get("default_password") == "password"
        assert model.get("group_$222_ids") == [1]
        assert model.get("group_$_ids") == ["222"]
        assert model.get("group_ids") is None
        assert model.get("vote_delegations_$222_from_ids") == [7]
        assert model.get("vote_delegations_$_from_ids") == ["222"]
        assert model.get("vote_delegations_from_ids") is None
        assert model.get("comment_$222") == "comment&lt;iframe&gt;&lt;/iframe&gt;"
        assert model.get("comment_$") == ["222"]
        assert model.get("number_$222") == "number"
        assert model.get("number_$") == ["222"]
        assert model.get("structure_level_$222") == "level"
        assert model.get("structure_level_$") == ["222"]
        assert model.get("about_me_$222") == "<p>about</p>&lt;iframe&gt;&lt;/iframe&gt;"
        assert model.get("about_me_$") == ["222"]
        assert model.get("vote_weight_$222") == "1.000000"
        assert model.get("vote_weight_$") == ["222"]
        # check meeting.user_ids
        meeting = self.get_model("meeting/222")
        assert meeting.get("user_ids") == [8]

    def test_create_invalid_present_meeting(self) -> None:
        self.set_models({"meeting/1": {}, "meeting/2": {}})
        response = self.request(
            "user.create_temporary",
            {
                "username": "test_Xcdfgee",
                "meeting_id": 1,
                "is_present_in_meeting_ids": [2],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A temporary user can only be present in its respective meeting.",
            response.json["message"],
        )
        self.assert_model_not_exists("user/2")

    def test_create_invalid_group(self) -> None:
        self.set_models({"meeting/1": {}, "group/2": {"meeting_id": 2}})
        response = self.request(
            "user.create_temporary",
            {"username": "test_Xcdfgee", "meeting_id": 1, "group_ids": [2]},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Group 2 is not in the meeting of the temporary user.",
            response.json["message"],
        )
        self.assert_model_not_exists("user/2")

    def test_create_empty_data(self) -> None:
        response = self.request("user.create_temporary", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'username'] properties",
            response.json["message"],
        )
        self.assert_model_not_exists("user/2")

    def test_create_wrong_field(self) -> None:
        self.create_model("meeting/222", {"name": "name_shjeuazu"})
        response = self.request(
            "user.create_temporary",
            {
                "wrong_field": "text_AefohteiF8",
                "username": "test1",
                "meeting_id": 222,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )
        self.assert_model_not_exists("user/2")

    def test_create_invalid_vote_delegation(self) -> None:
        self.create_model("meeting/222")
        response = self.request(
            "user.create_temporary",
            {
                "username": "test_Xcdfgee",
                "meeting_id": 222,
                "vote_delegations_from_ids": [7],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following users were not found",
            response.json["message"],
        )
        self.assert_model_not_exists("user/2")

    def test_username_already_given(self) -> None:
        self.create_model("meeting/222")
        response = self.request(
            "user.create_temporary", {"username": "admin", "meeting_id": 222}
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"] == "A user with the username admin already exists."
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "user.create_temporary",
            {"username": "permission_test_user", "meeting_id": 1},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {},
            "user.create_temporary",
            {"username": "permission_test_user", "meeting_id": 1},
            Permissions.User.CAN_MANAGE,
        )
