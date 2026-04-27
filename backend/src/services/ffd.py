import uuid


def ffd(labels: list[dict], truck_capacity_tons: float, max_iterations: int = 1000) -> list[dict]:
    """First Fit Decreasing bin-packing on volume_tons. Returns list of bin dicts."""
    eligible = [l for l in labels if l["volume_tons"] > 0 and l["volume_tons"] <= truck_capacity_tons]
    sorted_labels = sorted(eligible, key=lambda l: l["volume_tons"], reverse=True)

    bins: list[dict] = []
    capped = False

    for i, label in enumerate(sorted_labels):
        if i >= max_iterations:
            capped = True
            break

        placed = False
        for bin_ in bins:
            if round(bin_["totalTons"] + label["volume_tons"], 4) <= truck_capacity_tons:
                bin_["items"].append(label)
                bin_["totalTons"] = round(bin_["totalTons"] + label["volume_tons"], 4)
                bin_["totalPcs"] += label["piece_count"]
                placed = True
                break

        if not placed:
            bins.append({
                "_id": f"GEN-{uuid.uuid4().hex[:12]}",
                "items": [label],
                "totalTons": round(label["volume_tons"], 4),
                "totalPcs": label["piece_count"],
                "partial": False,
                "destination": "",
            })

    if capped:
        for bin_ in bins:
            bin_["partial"] = True

    return bins
