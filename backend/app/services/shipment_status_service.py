class InvalidShipmentTransitionError(Exception):
    pass


VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft":      {"confirmed", "cancelled"},
    "confirmed":  {"loading", "cancelled"},
    "loading":    {"dispatched", "cancelled"},
    "dispatched": {"delivered"},
    "delivered":  set(),
    "cancelled":  set(),
}


class ShipmentStatusService:
    @staticmethod
    def transition(current: str, new: str) -> str:
        if current not in VALID_TRANSITIONS:
            raise InvalidShipmentTransitionError(f"Unknown status: '{current}'")
        if new not in VALID_TRANSITIONS:
            raise InvalidShipmentTransitionError(f"Unknown status: '{new}'")
        if new not in VALID_TRANSITIONS[current]:
            raise InvalidShipmentTransitionError(f"Invalid transition: '{current}' → '{new}'")
        return new
