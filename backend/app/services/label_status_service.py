class InvalidTransitionError(Exception):
    pass


VALID_TRANSITIONS: dict[str, set[str]] = {
    "available":   {"reserved", "idle", "damaged"},
    "reserved":    {"in_transit", "in_shipment", "available", "idle", "damaged"},
    "in_transit":  {"available", "idle", "damaged"},
    "in_shipment": {"delivered", "idle", "damaged"},
    "idle":        {"available", "damaged"},
    "delivered":   set(),
    "damaged":     set(),
}


class LabelStatusService:
    @staticmethod
    def transition(current: str, new: str) -> str:
        if current not in VALID_TRANSITIONS:
            raise InvalidTransitionError(f"Unknown status: '{current}'")
        if new not in VALID_TRANSITIONS:
            raise InvalidTransitionError(f"Unknown status: '{new}'")
        if new not in VALID_TRANSITIONS[current]:
            raise InvalidTransitionError(f"Invalid transition: '{current}' → '{new}'")
        return new
