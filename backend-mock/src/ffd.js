/**
 * First Fit Decreasing bin-packing.
 * Primary metric: volume_tons. Items exceeding truckCapacityTons are skipped.
 * Returns an array of bin objects (one per truck load plan).
 */
function ffd(labels, truckCapacityTons, maxIterations = 1000) {
  const ts      = Date.now();
  const eligible = labels.filter(l => l.volume_tons > 0 && l.volume_tons <= truckCapacityTons);
  const sorted   = [...eligible].sort((a, b) => b.volume_tons - a.volume_tons);

  const bins = [];
  let iterations = 0;

  for (const label of sorted) {
    if (++iterations > maxIterations) break;

    let placed = false;
    for (const bin of bins) {
      if (bin.totalTons + label.volume_tons <= truckCapacityTons) {
        bin.items.push(label);
        bin.totalTons  = parseFloat((bin.totalTons  + label.volume_tons).toFixed(4));
        bin.totalPcs  += label.piece_count;
        placed = true;
        break;
      }
    }

    if (!placed) {
      bins.push({
        _id:       `GEN-${ts}-${String(bins.length + 1).padStart(3, '0')}`,
        items:     [label],
        totalTons: parseFloat(label.volume_tons.toFixed(4)),
        totalPcs:  label.piece_count,
        partial:   false,
        destination: '',
      });
    }
  }

  return bins;
}

module.exports = { ffd };
