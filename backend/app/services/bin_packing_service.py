from dataclasses import dataclass, field

from app.schemas.bin_packing import LabelInput, PackingFilters, TruckInput


@dataclass
class LoadPlanItem:
    progressivo: str
    volume_tons: float


@dataclass
class LoadPlan:
    items: list[LoadPlanItem] = field(default_factory=list)
    total_weight_tons: float = 0.0
    partial: bool = False


class BinPackingService:
    @staticmethod
    def pack(
        labels: list[LabelInput],
        truck: TruckInput,
        filters: PackingFilters,
        max_iterations: int | None = None,
    ) -> LoadPlan:
        candidates = [l for l in labels if l.market_type == "ME"]
        if filters.country is not None:
            candidates = [l for l in candidates if l.country == filters.country]
        if filters.order_condition is not None:
            candidates = [l for l in candidates if l.order_condition == filters.order_condition]
        if filters.exit_date_from is not None or filters.exit_date_to is not None:
            candidates = [l for l in candidates if l.exit_date is not None]
        if filters.exit_date_from is not None:
            candidates = [l for l in candidates if l.exit_date >= filters.exit_date_from]
        if filters.exit_date_to is not None:
            candidates = [l for l in candidates if l.exit_date <= filters.exit_date_to]
        candidates.sort(key=lambda l: l.volume_tons, reverse=True)

        items: list[LoadPlanItem] = []
        total = 0.0
        partial = False

        for i, label in enumerate(candidates):
            if max_iterations is not None and i >= max_iterations:
                partial = True
                break
            if total + label.volume_tons <= truck.max_weight_tons:
                items.append(LoadPlanItem(progressivo=label.progressivo, volume_tons=label.volume_tons))
                total += label.volume_tons

        return LoadPlan(items=items, total_weight_tons=total, partial=partial)
