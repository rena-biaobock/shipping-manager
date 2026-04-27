import pytest
from src.services.ffd import ffd


def label(progressivo, volume_tons, piece_count=10):
    return {
        "progressivo": progressivo,
        "volume_tons": volume_tons,
        "piece_count": piece_count,
        "item_code": "TEST",
        "description": f"item-{progressivo}",
        "customer": "ACME",
        "status": "reserved",
    }


def test_packs_items_within_capacity():
    bins = ffd([label("A", 10), label("B", 8), label("C", 7), label("D", 3)], 15)
    assert len(bins) >= 2
    for bin_ in bins:
        assert bin_["totalTons"] <= 15


def test_all_items_fit_when_sum_equals_capacity():
    bins = ffd([label("A", 10), label("B", 5)], 15)
    assert len(bins) == 1
    assert bins[0]["totalTons"] == 15


def test_excludes_items_exceeding_truck_capacity():
    bins = ffd([label("A", 50), label("B", 5)], 10)
    assert len(bins) == 1
    assert bins[0]["items"][0]["progressivo"] == "B"


def test_returns_empty_array_for_empty_input():
    assert ffd([], 27) == []


def test_returns_empty_when_all_items_exceed_capacity():
    assert ffd([label("A", 100), label("B", 200)], 27) == []


def test_respects_max_iterations_cap():
    labels = [label(str(i), 1) for i in range(100)]
    bins = ffd(labels, 27, 10)
    total_items = sum(len(b["items"]) for b in bins)
    assert total_items <= 10, f"Expected ≤10 items processed, got {total_items}"


def test_unique_id_per_bin():
    labels = [label(str(i), 10) for i in range(5)]
    ids = [b["_id"] for b in ffd(labels, 10)]
    assert len(set(ids)) == len(ids), "Duplicate _id detected"


def test_accumulates_total_pcs_correctly():
    bins = ffd([label("A", 5, 20), label("B", 5, 30)], 15)
    assert len(bins) == 1
    assert bins[0]["totalPcs"] == 50


def test_sorts_descending_large_items_first():
    bins = ffd([label("small", 1), label("big", 9)], 10)
    assert len(bins) == 1
    assert bins[0]["items"][0]["progressivo"] == "big"
