"""
Unit tests for LabelStatusService.

State machine:

  Company leg:
    available → reserved → in_transit → available (at terminal)

  Terminal / customer leg:
    available → reserved → in_shipment → delivered  (terminal)

  Rollback:
    reserved → available

  Manual damage (any active state):
    available | reserved | in_transit | in_shipment → damaged

  Terminal states (no exit):
    delivered, damaged

Note: idle is not a status. avg_days_idle is a plain informational field.
"""

import pytest

from app.services.label_status_service import LabelStatusService, InvalidTransitionError


# ---------------------------------------------------------------------------
# Valid transitions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("current, new", [
    # company leg
    ("available",   "reserved"),
    ("reserved",    "in_transit"),
    ("in_transit",  "available"),
    # terminal / customer leg
    ("reserved",    "in_shipment"),
    ("in_shipment", "delivered"),
    # rollback
    ("reserved",    "available"),
    # damaged
    ("available",   "damaged"),
    ("reserved",    "damaged"),
    ("in_transit",  "damaged"),
    ("in_shipment", "damaged"),
])
def test_valid_transition_returns_new_status(current, new):
    result = LabelStatusService.transition(current, new)
    assert result == new


# ---------------------------------------------------------------------------
# Invalid transitions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("current, new", [
    # skipping steps
    ("available",   "in_transit"),
    ("available",   "in_shipment"),
    ("available",   "delivered"),
    ("reserved",    "delivered"),
    # backwards / wrong leg
    ("in_transit",  "reserved"),
    ("in_transit",  "in_shipment"),
    ("in_shipment", "available"),
    ("in_shipment", "reserved"),
    ("in_shipment", "in_transit"),
    # out of terminal states
    ("delivered",   "available"),
    ("delivered",   "reserved"),
    ("delivered",   "in_transit"),
    ("delivered",   "in_shipment"),
    ("delivered",   "damaged"),
    ("damaged",     "available"),
    ("damaged",     "reserved"),
    ("damaged",     "in_transit"),
    ("damaged",     "in_shipment"),
    ("damaged",     "delivered"),
])
def test_invalid_transition_raises(current, new):
    with pytest.raises(InvalidTransitionError):
        LabelStatusService.transition(current, new)


# ---------------------------------------------------------------------------
# Unknown and self-transition
# ---------------------------------------------------------------------------

def test_unknown_current_status_raises():
    with pytest.raises(InvalidTransitionError):
        LabelStatusService.transition("nonexistent", "available")


def test_unknown_new_status_raises():
    with pytest.raises(InvalidTransitionError):
        LabelStatusService.transition("available", "nonexistent")


def test_self_transition_raises():
    with pytest.raises(InvalidTransitionError):
        LabelStatusService.transition("available", "available")
