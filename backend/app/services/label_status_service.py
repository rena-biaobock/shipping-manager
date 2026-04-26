class InvalidTransitionError(Exception):
    pass


VALID_TRANSITIONS: dict[str, set[str]] = {
    "available":   {"reserved", "damaged"},
    "reserved":    {"in_transit", "in_shipment", "available", "damaged"},
    "in_transit":  {"available", "damaged"},
    "in_shipment": {"delivered", "damaged"},
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
