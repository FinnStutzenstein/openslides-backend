from tests.system.action.base import BaseActionTestCase


class ProjectorAddToPreview(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {},
                "meeting/2": {},
                "assignment/1": {"meeting_id": 1},
                "projector/1": {"meeting_id": 1, "preview_projection_ids": [10]},
                "projector/2": {"meeting_id": 1, "preview_projection_ids": [11, 12]},
                "projector/3": {"meeting_id": 1},
                "projector/4": {"meeting_id": 2},
                "projection/10": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/1",
                    "preview_projector_id": 1,
                    "weight": 10,
                },
                "projection/11": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/1",
                    "preview_projector_id": 2,
                    "weight": 20,
                },
                "projection/12": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/1",
                    "preview_projector_id": 2,
                    "weight": 30,
                },
            }
        )

    def test_add_to_preview(self) -> None:
        response = self.request(
            "projector.add_to_preview",
            {"ids": [1, 2], "content_object_id": "assignment/1", "stable": False},
        )
        self.assert_status_code(response, 200)
        projector_1 = self.get_model("projector/1")
        assert projector_1.get("preview_projection_ids") == [10, 13]
        projector_2 = self.get_model("projector/2")
        assert projector_2.get("preview_projection_ids") == [11, 12, 14]
        projection_13 = self.get_model("projection/13")
        assert projection_13.get("preview_projector_id") == 1
        assert projection_13.get("content_object_id") == "assignment/1"
        assert projection_13.get("weight") == 11
        projection_14 = self.get_model("projection/14")
        assert projection_14.get("preview_projector_id") == 2
        assert projection_14.get("content_object_id") == "assignment/1"
        assert projection_14.get("weight") == 31

    def test_add_to_preview_empty_projector(self) -> None:
        response = self.request(
            "projector.add_to_preview",
            {"ids": [3], "content_object_id": "assignment/1", "stable": False},
        )
        self.assert_status_code(response, 200)
        projector_1 = self.get_model("projector/3")
        assert projector_1.get("preview_projection_ids") == [13]
        projection_13 = self.get_model("projection/13")
        assert projection_13.get("preview_projector_id") == 3
        assert projection_13.get("content_object_id") == "assignment/1"
        assert projection_13.get("weight") == 2

    def test_add_to_preview_non_unique_ids(self) -> None:
        response = self.request(
            "projector.add_to_preview",
            {"ids": [1, 1], "content_object_id": "assignment/1", "stable": False},
        )
        self.assert_status_code(response, 400)
        assert "data.ids must contain unique items" in response.json["message"]

    def test_add_to_preview_check_meeting_id(self) -> None:
        response = self.request(
            "projector.add_to_preview",
            {"ids": [4], "content_object_id": "assignment/1", "stable": False},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['projector/4']",
            response.json["message"],
        )
