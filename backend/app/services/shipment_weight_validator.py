class CapacityExceededError(Exception):
    def __init__(self, total: float, max_weight_tons: float) -> None:
        self.total = total
        self.overage = round(total - max_weight_tons, 10)
        super().__init__(
            f"Total weight {total} t exceeds capacity {max_weight_tons} t "
            f"by {self.overage} t"
        )


class ShipmentWeightValidator:
    @staticmethod
    def validate(label_weights: list[float], max_weight_tons: float) -> float:
        total = sum(label_weights)
        if total > max_weight_tons:
            raise CapacityExceededError(total, max_weight_tons)
        return total
