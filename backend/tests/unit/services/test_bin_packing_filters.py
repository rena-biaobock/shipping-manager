"""
Unit tests for PackingFilters: country and order_condition.

Rules under test:
- country filter: when set, only labels with a matching country are packed
- order_condition filter: when set, only labels with a matching condition are packed
- both filters can be combined — label must pass all active filters
- filters set to None are not applied (no restriction)
"""

import pytest

from app.services.bin_packing_service import BinPackingService
from app.schemas.bin_packing import LabelInput, TruckInput, PackingFilters


def make_truck(max_weight_tons: float = 100.0) -> TruckInput:
    return TruckInput(id="truck-1", max_weight_tons=max_weight_tons)


def make_label(
    progressivo: str,
    volume_tons: float = 1.0,
    market_type: str = "ME",
    country: str = "Paraguay",
    order_condition: str = "pedido_ate_hoje",
) -> LabelInput:
    return LabelInput(
        progressivo=progressivo,
        volume_tons=volume_tons,
        market_type=market_type,
        country=country,
        order_condition=order_condition,
    )


# ---------------------------------------------------------------------------
# Country filter
# ---------------------------------------------------------------------------

def test_country_filter_excludes_labels_from_other_countries():
    truck = make_truck()
    labels = [
        make_label("py-1", country="Paraguay"),
        make_label("br-1", country="Brasil"),
    ]
    filters = PackingFilters(country="Paraguay")
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    packed = {item.progressivo for item in result.items}
    assert "py-1" in packed
    assert "br-1" not in packed


def test_country_filter_none_includes_all_countries():
    truck = make_truck()
    labels = [
        make_label("py-1", country="Paraguay"),
        make_label("uy-1", country="Uruguay"),
        make_label("ar-1", country="Argentina"),
    ]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    assert {item.progressivo for item in result.items} == {"py-1", "uy-1", "ar-1"}


def test_country_filter_no_match_returns_empty_plan():
    truck = make_truck()
    labels = [
        make_label("br-1", country="Brasil"),
        make_label("br-2", country="Brasil"),
    ]
    filters = PackingFilters(country="Paraguay")
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    assert result.items == []
    assert result.total_weight_tons == 0.0


# ---------------------------------------------------------------------------
# Order condition filter
# ---------------------------------------------------------------------------

def test_order_condition_filter_excludes_other_conditions():
    truck = make_truck()
    labels = [
        make_label("due-today", order_condition="pedido_ate_hoje"),
        make_label("future",    order_condition="fixo_futuro"),
    ]
    filters = PackingFilters(order_condition="pedido_ate_hoje")
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    packed = {item.progressivo for item in result.items}
    assert "due-today" in packed
    assert "future" not in packed


def test_order_condition_filter_none_includes_all_conditions():
    truck = make_truck()
    labels = [
        make_label("a", order_condition="pedido_ate_hoje"),
        make_label("b", order_condition="fixo_futuro"),
        make_label("c", order_condition="antecipa_mes_atual"),
    ]
    result = BinPackingService.pack(labels=labels, truck=truck, filters=PackingFilters())
    assert {item.progressivo for item in result.items} == {"a", "b", "c"}


def test_order_condition_filter_no_match_returns_empty_plan():
    truck = make_truck()
    labels = [make_label("a", order_condition="fixo_futuro")]
    filters = PackingFilters(order_condition="pedido_ate_hoje")
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    assert result.items == []


# ---------------------------------------------------------------------------
# Combined filters
# ---------------------------------------------------------------------------

def test_country_and_order_condition_filters_are_combined():
    """Label must pass both filters to be packed."""
    truck = make_truck()
    labels = [
        make_label("pass",          country="Paraguay", order_condition="pedido_ate_hoje"),
        make_label("wrong-country", country="Brasil",   order_condition="pedido_ate_hoje"),
        make_label("wrong-cond",    country="Paraguay", order_condition="fixo_futuro"),
        make_label("both-wrong",    country="Brasil",   order_condition="fixo_futuro"),
    ]
    filters = PackingFilters(country="Paraguay", order_condition="pedido_ate_hoje")
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    assert [item.progressivo for item in result.items] == ["pass"]


def test_me_filter_still_applied_with_other_filters():
    """ME-only rule is always enforced even when other filters are active."""
    truck = make_truck()
    labels = [
        make_label("export", market_type="ME", country="Paraguay"),
        make_label("domestic", market_type="MI", country="Paraguay"),
    ]
    filters = PackingFilters(country="Paraguay")
    result = BinPackingService.pack(labels=labels, truck=truck, filters=filters)
    packed = {item.progressivo for item in result.items}
    assert "export" in packed
    assert "domestic" not in packed
