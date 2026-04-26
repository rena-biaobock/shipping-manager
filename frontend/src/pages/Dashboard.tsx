import { useQuery } from '@tanstack/react-query'
import { stockLabelsService } from '../services/stockLabels'
import { shipmentsService } from '../services/shipments'

export default function Dashboard() {
  const { data: labels = [] } = useQuery({
    queryKey: ['stock-labels'],
    queryFn: () => stockLabelsService.list(),
  })
  const { data: shipments = [] } = useQuery({
    queryKey: ['shipments'],
    queryFn: () => shipmentsService.list(),
  })

  const totalTons = labels.reduce((sum, l) => sum + parseFloat(l.volume_tons), 0)
  const available = labels.filter((l) => l.status === 'available').length
  const reserved = labels.filter((l) => l.status === 'reserved').length
  const activeShipments = shipments.filter((s) => s.status !== 'delivered' && s.status !== 'cancelled').length

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard label="Total Labels" value={labels.length} />
        <KpiCard label="Total Tons" value={totalTons.toFixed(3)} />
        <KpiCard label="Available" value={available} />
        <KpiCard label="Reserved" value={reserved} />
        <KpiCard label="Active Shipments" value={activeShipments} />
      </div>
    </div>
  )
}

function KpiCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  )
}
