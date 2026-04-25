"""
Unit tests for ShipmentStatusService.

State machine:

  draft → confirmed → loading → dispatched → delivered  (terminal)
    ↓           ↓          ↓
  cancelled  cancelled  cancelled                        (terminal)

Once dispatched the shipment is on the road — cancellation is no longer allowed.
delivered and cancelled are terminal states with no exit.
"""

import pytest

from app.services.shipment_status_service import ShipmentStatusService, InvalidShipmentTransitionError


# ---------------------------------------------------------------------------
# Valid transitions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("current, new", [
    ("draft",       "confirmed"),
    ("draft",       "cancelled"),
    ("confirmed",   "loading"),
    ("confirmed",   "cancelled"),
    ("loading",     "dispatched"),
    ("loading",     "cancelled"),
    ("dispatched",  "delivered"),
])
def test_valid_transition_returns_new_status(current, new):
    result = ShipmentStatusService.transition(current, new)
    assert result == new


# ---------------------------------------------------------------------------
# Invalid transitions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("current, new", [
    # skipping steps
    ("draft",       "loading"),
    ("draft",       "dispatched"),
    ("draft",       "delivered"),
    ("confirmed",   "dispatched"),
    ("confirmed",   "delivered"),
    ("loading",     "delivered"),
    # backwards
    ("confirmed",   "draft"),
    ("loading",     "draft"),
    ("loading",     "confirmed"),
    ("dispatched",  "draft"),
    ("dispatched",  "confirmed"),
    ("dispatched",  "loading"),
    # too late to cancel
    ("dispatched",  "cancelled"),
    # out of terminal states
    ("delivered",   "draft"),
    ("delivered",   "confirmed"),
    ("delivered",   "loading"),
    ("delivered",   "dispatched"),
    ("delivered",   "cancelled"),
    ("cancelled",   "draft"),
    ("cancelled",   "confirmed"),
    ("cancelled",   "loading"),
    ("cancelled",   "dispatched"),
    ("cancelled",   "delivered"),
])
def test_invalid_transition_raises(current, new):
    with pytest.raises(InvalidShipmentTransitionError):
        ShipmentStatusService.transition(current, new)


# ---------------------------------------------------------------------------
# Unknown and self-transition
# ---------------------------------------------------------------------------

def test_unknown_current_status_raises():
    with pytest.raises(InvalidShipmentTransitionError):
        ShipmentStatusService.transition("nonexistent", "confirmed")


def test_unknown_new_status_raises():
    with pytest.raises(InvalidShipmentTransitionError):
        ShipmentStatusService.transition("draft", "nonexistent")


def test_self_transition_raises():
    with pytest.raises(InvalidShipmentTransitionError):
        ShipmentStatusService.transition("draft", "draft")
