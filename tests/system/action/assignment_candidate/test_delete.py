from tests.system.action.base import BaseActionTestCase


class AssignmentCandidateDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/1333": {
                    "name": "name_JhlFOAfK",
                    "assignment_candidate_ids": [111],
                },
                "user/110": {
                    "assignment_candidate_$1333_ids": [111],
                    "assignment_candidate_$_ids": ["1333"],
                },
                "assignment/111": {
                    "title": "title_xTcEkItp",
                    "meeting_id": 1333,
                    "candidate_ids": [111],
                },
                "assignment_candidate/111": {
                    "user_id": 110,
                    "assignment_id": 111,
                    "meeting_id": 1333,
                },
            }
        )
        response = self.request("assignment_candidate.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("assignment_candidate/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/1333": {
                    "name": "name_JhlFOAfK",
                    "assignment_candidate_ids": [112],
                },
                "user/110": {
                    "assignment_candidate_$1333_ids": [112],
                    "assignment_candidate_$_ids": ["1333"],
                },
                "assignment/111": {
                    "title": "title_xTcEkItp",
                    "meeting_id": 1333,
                    "candidate_ids": [111],
                },
                "assignment_candidate/112": {
                    "user_id": 110,
                    "assignment_id": 111,
                    "meeting_id": 1333,
                },
            }
        )

        response = self.request("assignment_candidate.delete", {"id": 111})
        self.assert_status_code(response, 400)
        assert "Model 'assignment_candidate/111' does not exist." in str(
            response.json["message"]
        )
        model = self.get_model("assignment_candidate/112")
        assert model.get("user_id") == 110
        assert model.get("assignment_id") == 111

    def test_delete_finished(self) -> None:
        self.set_models(
            {
                "meeting/1333": {
                    "name": "name_JhlFOAfK",
                    "assignment_candidate_ids": [111],
                },
                "user/110": {
                    "assignment_candidate_$1333_ids": [111],
                    "assignment_candidate_$_ids": ["1333"],
                },
                "assignment/111": {
                    "title": "title_xTcEkItp",
                    "meeting_id": 1333,
                    "candidate_ids": [111],
                    "phase": "finished",
                },
                "assignment_candidate/111": {
                    "user_id": 110,
                    "assignment_id": 111,
                    "meeting_id": 1333,
                },
            }
        )
        response = self.request("assignment_candidate.delete", {"id": 111})

        self.assert_status_code(response, 400)
        self.assert_model_exists("assignment_candidate/111")
        self.assertIn(
            "It is not permitted to remove a candidate from a finished assignment!",
            response.json["message"],
        )
