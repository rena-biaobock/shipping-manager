"""
Unit tests for ShipmentWeightValidator.

Rules under test:
- Total volume_tons of assigned labels must not exceed truck max_weight_tons
- Raises CapacityExceededError with the overage when the limit is breached
- Returns the exact total when within capacity
- Empty label list is valid (total = 0)
"""

import pytest

from app.services.shipment_weight_validator import (
    ShipmentWeightValidator,
    CapacityExceededError,
)


# ---------------------------------------------------------------------------
# Within capacity
# ---------------------------------------------------------------------------

def test_empty_labels_returns_zero():
    total = ShipmentWeightValidator.validate(label_weights=[], max_weight_tons=30.0)
    assert total == pytest.approx(0.0)


def test_labels_within_capacity_returns_total():
    total = ShipmentWeightValidator.validate(
        label_weights=[5.0, 10.0, 8.0],
        max_weight_tons=30.0,
    )
    assert total == pytest.approx(23.0)


def test_total_exactly_at_capacity_is_valid():
    total = ShipmentWeightValidator.validate(
        label_weights=[15.0, 15.0],
        max_weight_tons=30.0,
    )
    assert total == pytest.approx(30.0)


def test_single_label_within_capacity():
    total = ShipmentWeightValidator.validate(
        label_weights=[0.322],
        max_weight_tons=30.0,
    )
    assert total == pytest.approx(0.322)


# ---------------------------------------------------------------------------
# Capacity exceeded
# ---------------------------------------------------------------------------

def test_total_over_capacity_raises():
    with pytest.raises(CapacityExceededError):
        ShipmentWeightValidator.validate(
            label_weights=[20.0, 15.0],
            max_weight_tons=30.0,
        )


def test_capacity_exceeded_error_contains_overage():
    with pytest.raises(CapacityExceededError) as exc_info:
        ShipmentWeightValidator.validate(
            label_weights=[20.0, 15.0],
            max_weight_tons=30.0,
        )
    assert exc_info.value.overage == pytest.approx(5.0)


def test_capacity_exceeded_error_contains_total():
    with pytest.raises(CapacityExceededError) as exc_info:
        ShipmentWeightValidator.validate(
            label_weights=[20.0, 15.0],
            max_weight_tons=30.0,
        )
    assert exc_info.value.total == pytest.approx(35.0)


def test_single_label_over_capacity_raises():
    with pytest.raises(CapacityExceededError):
        ShipmentWeightValidator.validate(
            label_weights=[31.0],
            max_weight_tons=30.0,
        )


def test_fractional_overage_raises():
    with pytest.raises(CapacityExceededError) as exc_info:
        ShipmentWeightValidator.validate(
            label_weights=[29.9, 0.2],
            max_weight_tons=30.0,
        )
    assert exc_info.value.overage == pytest.approx(0.1)
