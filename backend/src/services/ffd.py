import time


def ffd(labels: list[dict], truck_capacity_tons: float, max_iterations: int = 1000) -> list[dict]:
    """First Fit Decreasing bin-packing on volume_tons. Returns list of bin dicts."""
    eligible = [l for l in labels if l["volume_tons"] > 0 and l["volume_tons"] <= truck_capacity_tons]
    sorted_labels = sorted(eligible, key=lambda l: l["volume_tons"], reverse=True)

    bins: list[dict] = []
    ts = int(time.time() * 1000)
    iterations = 0

    for label in sorted_labels:
        iterations += 1
        if iterations > max_iterations:
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
                "_id": f"GEN-{ts}-{str(len(bins) + 1).zfill(3)}",
                "items": [label],
                "totalTons": round(label["volume_tons"], 4),
                "totalPcs": label["piece_count"],
                "partial": False,
                "destination": "",
            })

    return bins
