import fastjsonschema  # type: ignore

from ...models.meeting import Meeting
from ...shared.permissions.meeting import MEETING_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..generics import CreateAction

create_meeting_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "New meetings schema",
        "description": "An array of new meetings.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "committee_id": Meeting().get_schema("committee_id"),
                "title": Meeting().get_schema("title"),
            },
            "required": ["committee_id", "title"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("meeting.create")
class MeetingCreate(CreateAction):
    """
    Action to create meetings.
    """

    model = Meeting()
    schema = create_meeting_schema
    permission_reference = "committee_id"
    manage_permission = MEETING_CAN_MANAGE