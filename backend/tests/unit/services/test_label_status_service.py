"""
Unit tests for LabelStatusService.

State machine:

  Company leg:
    available → reserved → in_transit → available (at terminal)

  Terminal leg:
    available → reserved → in_shipment → delivered  (terminal)

  Unassign / rollback:
    reserved → available

  Watchdog (automated):
    available | reserved | in_transit | in_shipment | idle → idle

  Manual damage:
    available | reserved | in_transit | in_shipment | idle → damaged

  Terminal states (no exit):
    delivered, damaged

Note: order assignment comes from the ERP import and is not a guard here.
"reserved" means selected for a specific truck load, not "has an order".
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
    # watchdog → idle
    ("available",   "idle"),
    ("reserved",    "idle"),
    ("in_transit",  "idle"),
    ("in_shipment", "idle"),
    # idle recovery
    ("idle",        "available"),
    # damaged
    ("available",   "damaged"),
    ("reserved",    "damaged"),
    ("in_transit",  "damaged"),
    ("in_shipment", "damaged"),
    ("idle",        "damaged"),
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
    # backwards / illegal
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
    ("delivered",   "idle"),
    ("delivered",   "damaged"),
    ("damaged",     "available"),
    ("damaged",     "reserved"),
    ("damaged",     "in_transit"),
    ("damaged",     "in_shipment"),
    ("damaged",     "delivered"),
    ("damaged",     "idle"),
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
