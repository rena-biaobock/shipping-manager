"""
Unit tests for BinPackingService.

Domain rules under test:
- Only ME (Mercado Externo / export) labels are ever considered — MI labels are always excluded
- Primary packing metric: volume_tons (FFD — sort descending, fit first truck that has room)
- Hard aggregate constraint: sum(volume_tons) <= truck.max_weight_tons
- Result is flagged partial=True when max_iterations cap is reached before all labels are placed
"""

import pytest

from app.services.bin_packing_service import BinPackingService, LoadPlan, LoadPlanItem
from app.schemas.bin_packing import LabelInput, TruckInput, PackingFilters


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_truck(
    max_weight_tons: float = 30.0,
    truck_id: str = "truck-1",
) -> TruckInput:
    return TruckInput(id=truck_id, max_weight_tons=max_weight_tons)


def make_label(
    progressivo: str,
    volume_tons: float,
    market_type: str = "ME",
    order_condition: str = "pedido_ate_hoje",
) -> LabelInput:
    return LabelInput(
        progressivo=progressivo,
        volume_tons=volume_tons,
        market_type=market_type,
        order_condition=order_condition,
    )


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------

def test_empty_label_list_returns_empty_plan():
    truck = make_truck()
    result = BinPackingService.pack(labels=[], truck=truck, filters=PackingFilters())
    assert result.items == []
    assert result.total_weight_tons == 0.0
    assert result.partial is False


# ---------------------------------------------------------------------------
# All labels fit
# ---------------------------------------------------------------------------

def test_labels_within_capacity_are_all_packed():
    truck = make_truck(max_weight_tons=10.0)
    labels = [
        make_label("A", volume_tons=3.0),
        make_label("B", volume_tons=3.0),
        make_label("C", volume_tons=3.0),
    ]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    assert {item.progressivo for item in result.items} == {"A", "B", "C"}
    assert result.total_weight_tons == pytest.approx(9.0)
    assert result.partial is False


# ---------------------------------------------------------------------------
# Capacity overflow — greedy stops when full
# ---------------------------------------------------------------------------

def test_labels_exceeding_capacity_stops_at_limit():
    truck = make_truck(max_weight_tons=10.0)
    labels = [
        make_label("A", volume_tons=4.0),
        make_label("B", volume_tons=4.0),
        make_label("C", volume_tons=4.0),  # would push total to 12 t — excluded
    ]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    packed = {item.progressivo for item in result.items}
    assert "C" not in packed
    assert result.total_weight_tons <= 10.0


# ---------------------------------------------------------------------------
# FFD ordering — heaviest labels packed first
# ---------------------------------------------------------------------------

def test_ffd_packs_heaviest_labels_first():
    """
    Truck capacity = 12 t. Labels: 6 t, 3 t, 2 t (input order: 2, 3, 6).
    FFD sorts descending → 6, 3, 2 → total 11 t ≤ 12 t. All three packed.
    """
    truck = make_truck(max_weight_tons=12.0)
    labels = [
        make_label("small", volume_tons=2.0),
        make_label("medium", volume_tons=3.0),
        make_label("large", volume_tons=6.0),
    ]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    assert {item.progressivo for item in result.items} == {"small", "medium", "large"}


def test_ffd_maximises_load_compared_to_first_fit_ascending():
    """
    Truck = 10 t. Labels: 6 t, 5 t, 4 t.
    Ascending order would pack 4 + 5 = 9 t, skip 6 t → 9 t total.
    FFD packs 6 + 4 = 10 t → 10 t total (better).
    """
    truck = make_truck(max_weight_tons=10.0)
    labels = [
        make_label("six", volume_tons=6.0),
        make_label("five", volume_tons=5.0),
        make_label("four", volume_tons=4.0),
    ]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    packed = {item.progressivo for item in result.items}
    assert "six" in packed
    assert result.total_weight_tons == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# Market type — always ME, MI labels are never packed
# ---------------------------------------------------------------------------

def test_mi_labels_are_always_excluded():
    truck = make_truck()
    labels = [
        make_label("domestic", volume_tons=1.0, market_type="MI"),
        make_label("export", volume_tons=1.0, market_type="ME"),
    ]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    packed = {item.progressivo for item in result.items}
    assert "export" in packed
    assert "domestic" not in packed


def test_all_mi_labels_returns_empty_plan():
    truck = make_truck()
    labels = [
        make_label("domestic-1", volume_tons=1.0, market_type="MI"),
        make_label("domestic-2", volume_tons=2.0, market_type="MI"),
    ]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    assert result.items == []
    assert result.total_weight_tons == 0.0


# ---------------------------------------------------------------------------
# max_iterations cap → partial result
# ---------------------------------------------------------------------------

def test_partial_flag_set_when_max_iterations_reached():
    truck = make_truck(max_weight_tons=1000.0)
    labels = [make_label(str(i), volume_tons=0.1) for i in range(20)]
    result = BinPackingService.pack(
        labels=labels, truck=truck, filters=PackingFilters(), max_iterations=5
    )
    assert result.partial is True
    assert len(result.items) == 5


def test_no_partial_flag_when_all_labels_processed():
    truck = make_truck(max_weight_tons=1000.0)
    labels = [make_label(str(i), volume_tons=0.1) for i in range(5)]
    result = BinPackingService.pack(
        labels=labels, truck=truck, filters=PackingFilters(), max_iterations=100
    )
    assert result.partial is False
    assert len(result.items) == 5


# ---------------------------------------------------------------------------
# Result structure
# ---------------------------------------------------------------------------

def test_load_plan_item_carries_progressivo_and_volume():
    truck = make_truck()
    labels = [make_label("X", volume_tons=2.5)]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    item = result.items[0]
    assert isinstance(item, LoadPlanItem)
    assert item.progressivo == "X"
    assert item.volume_tons == pytest.approx(2.5)


def test_total_weight_is_sum_of_packed_items():
    truck = make_truck(max_weight_tons=10.0)
    labels = [
        make_label("A", volume_tons=2.0),
        make_label("B", volume_tons=3.5),
    ]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    assert result.total_weight_tons == pytest.approx(5.5)
