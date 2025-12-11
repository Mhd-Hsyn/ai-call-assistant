# services/workflow_mapper.py
from typing import List, Dict, Any


# Static per-state templates that ensure keys are present and in the expected order
# We implement a flexible generator: given incoming state entry (with name),
# choose the appropriate template and fill dynamic values.

def _sanitize_str(x):
    # ensure string; Retell wants strings not None
    if x is None:
        return ""
    return str(x)


def build_introduction_state(payload_item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": "introduction",
        "state_prompt": _sanitize_str(payload_item.get("state_prompt", "")),
        "edges": [
            {
                "destination_state_name": "information_collection",
                "description": _sanitize_str(payload_item.get("description", "")),
            }
        ],
        "tools": []
    }


def build_information_collection_state(payload_item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": "information_collection",
        "state_prompt": _sanitize_str(payload_item.get("state_prompt", "")),
        "edges": [
            {
                "destination_state_name": "check_availability",
                "description": _sanitize_str(payload_item.get("description", "")),
            }
        ],
        "tools": []
    }


def build_check_availability_state(payload_item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": "check_availability",
        "state_prompt": _sanitize_str(payload_item.get("state_prompt", "")),
        "tools": [
            {
                "type": "check_availability_cal",
                "name": "check_availability",
                "description": _sanitize_str(payload_item.get("description", "Check availability.")),
                "cal_api_key": _sanitize_str(payload_item.get("cal_api_key", "")),
                "event_type_id": payload_item.get("event_type_id") or 0,
                "timezone": _sanitize_str(payload_item.get("timezone", ""))
            }
        ],
        "edges": [
            {
                "destination_state_name": "appointment_booking",
                "description": _sanitize_str(payload_item.get("description", "")),
            }
        ]
    }


def build_appointment_booking_state(payload_item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": "appointment_booking",
        "state_prompt": _sanitize_str(payload_item.get("state_prompt", "")),
        "tools": [
            {
                "type": "book_appointment_cal",
                "name": "book_appointment",
                "description": _sanitize_str(payload_item.get("description", "Book the appointment.")),
                "cal_api_key": _sanitize_str(payload_item.get("cal_api_key", "")),
                "event_type_id": payload_item.get("event_type_id") or 0,
                "timezone": _sanitize_str(payload_item.get("timezone", ""))
            }
        ],
        "edges": [
            {
                "destination_state_name": "end_conversation",
                "description": _sanitize_str(payload_item.get("description", "")),
            }
        ]
    }


def build_end_conversation_state() -> Dict[str, Any]:
    return {
        "name": "end_conversation",
        "state_prompt": "Confirm the booking details one last time, thank the user for choosing Propest AI, and say goodbye professionally. Then hang up.",
        "tools": [
            {
                "type": "end_call",
                "name": "hang_up_call",
                "description": "End the call."
            }
        ],
        "edges": []
    }


# Main mapper: accepts incoming list (client payload) and returns retell_states list
def map_payload_to_retell_states(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert incoming payload list (simple format) to Retell-compatible list.
    Each state created by its own builder function (keeps keys static).
    """
    name_to_builder = {
        "introduction": build_introduction_state,
        "information_collection": build_information_collection_state,
        "check_availability": build_check_availability_state,
        "appointment_booking": build_appointment_booking_state,
    }

    retell_states = []
    # We'll iterate over input order and build known states. Unknown states will be ignored.
    for item in data:
        name = (item.get("name") or "").strip()
        builder = name_to_builder.get(name)
        if builder:
            retell_states.append(builder(item))
        else:
            # If unknown state name, create a generic preserved structure to avoid losing data
            # but still ensure keys exist
            retell_states.append({
                "name": name or "unknown_state",
                "state_prompt": str(item.get("state_prompt", "")),
                "edges": [],
                "tools": []
            })

    # ensure end_conversation always appended exactly once
    if not any(s["name"] == "end_conversation" for s in retell_states):
        retell_states.append(build_end_conversation_state())

    return retell_states
