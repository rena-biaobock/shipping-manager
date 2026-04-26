"""
Unit tests for PackingFilters: exit_date range.

Rules under test:
- exit_date_from: excludes labels whose exit_date is before this date
- exit_date_to: excludes labels whose exit_date is after this date
- both bounds can be combined to define a closed range
- a label with exit_date=None is excluded when any date filter is active
  (no order date means the constraint cannot be verified)
- no date filter → all labels are included regardless of exit_date
"""

import pytest
from datetime import date

from app.services.bin_packing_service import BinPackingService
from app.schemas.bin_packing import LabelInput, TruckInput, PackingFilters


def make_truck(max_weight_tons: float = 100.0) -> TruckInput:
    return TruckInput(id="truck-1", max_weight_tons=max_weight_tons)


def make_label(
    progressivo: str,
    volume_tons: float = 1.0,
    exit_date: date | None = date(2026, 5, 1),
) -> LabelInput:
    return LabelInput(
        progressivo=progressivo,
        volume_tons=volume_tons,
        market_type="ME",
        country="Paraguay",
        order_condition="pedido_ate_hoje",
        exit_date=exit_date,
    )


# ---------------------------------------------------------------------------
# exit_date_from
# ---------------------------------------------------------------------------

def test_exit_date_from_excludes_labels_before_that_date():
    truck = make_truck()
    labels = [
        make_label("early", exit_date=date(2026, 4, 30)),
        make_label("on-day", exit_date=date(2026, 5, 1)),
        make_label("late", exit_date=date(2026, 5, 10)),
    ]
    filters = PackingFilters(exit_date_from=date(2026, 5, 1))
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    packed = {item.progressivo for item in result.items}
    assert "early" not in packed
    assert "on-day" in packed
    assert "late" in packed


def test_exit_date_from_boundary_is_inclusive():
    truck = make_truck()
    labels = [make_label("boundary", exit_date=date(2026, 5, 1))]
    filters = PackingFilters(exit_date_from=date(2026, 5, 1))
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    assert result.items[0].progressivo == "boundary"


# ---------------------------------------------------------------------------
# exit_date_to
# ---------------------------------------------------------------------------

def test_exit_date_to_excludes_labels_after_that_date():
    truck = make_truck()
    labels = [
        make_label("early", exit_date=date(2026, 4, 20)),
        make_label("on-day", exit_date=date(2026, 5, 1)),
        make_label("late", exit_date=date(2026, 5, 2)),
    ]
    filters = PackingFilters(exit_date_to=date(2026, 5, 1))
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    packed = {item.progressivo for item in result.items}
    assert "early" in packed
    assert "on-day" in packed
    assert "late" not in packed


def test_exit_date_to_boundary_is_inclusive():
    truck = make_truck()
    labels = [make_label("boundary", exit_date=date(2026, 5, 1))]
    filters = PackingFilters(exit_date_to=date(2026, 5, 1))
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    assert result.items[0].progressivo == "boundary"


# ---------------------------------------------------------------------------
# Closed range (from + to)
# ---------------------------------------------------------------------------

def test_closed_range_packs_only_labels_within_window():
    truck = make_truck()
    labels = [
        make_label("before", exit_date=date(2026, 4, 29)),
        make_label("start",  exit_date=date(2026, 4, 30)),
        make_label("middle", exit_date=date(2026, 5, 5)),
        make_label("end",    exit_date=date(2026, 5, 10)),
        make_label("after",  exit_date=date(2026, 5, 11)),
    ]
    filters = PackingFilters(exit_date_from=date(2026, 4, 30), exit_date_to=date(2026, 5, 10))
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    packed = {item.progressivo for item in result.items}
    assert packed == {"start", "middle", "end"}
    assert "before" not in packed
    assert "after" not in packed


# ---------------------------------------------------------------------------
# Labels with exit_date=None
# ---------------------------------------------------------------------------

def test_label_with_no_exit_date_excluded_when_from_filter_is_active():
    truck = make_truck()
    labels = [
        make_label("no-date", exit_date=None),
        make_label("has-date", exit_date=date(2026, 5, 5)),
    ]
    filters = PackingFilters(exit_date_from=date(2026, 5, 1))
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    packed = {item.progressivo for item in result.items}
    assert "no-date" not in packed
    assert "has-date" in packed


def test_label_with_no_exit_date_excluded_when_to_filter_is_active():
    truck = make_truck()
    labels = [make_label("no-date", exit_date=None)]
    filters = PackingFilters(exit_date_to=date(2026, 5, 31))
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    assert result.items == []


def test_label_with_no_exit_date_packed_when_no_date_filter():
    truck = make_truck()
    labels = [make_label("no-date", exit_date=None)]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    assert result.items[0].progressivo == "no-date"


# ---------------------------------------------------------------------------
# No date filter
# ---------------------------------------------------------------------------

def test_no_date_filter_includes_all_exit_dates():
    truck = make_truck()
    labels = [
        make_label("past",   exit_date=date(2025, 1, 1)),
        make_label("today",  exit_date=date(2026, 4, 25)),
        make_label("future", exit_date=date(2027, 12, 31)),
    ]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    assert {item.progressivo for item in result.items} == {"past", "today", "future"}
