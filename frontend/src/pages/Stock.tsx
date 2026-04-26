import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { stockLabelsService } from '../services/stockLabels'
import type { LabelStatus, StockLabel } from '../types'

const STATUS_OPTIONS: LabelStatus[] = ['available', 'reserved', 'in_transit', 'in_shipment', 'delivered', 'damaged']

export default function Stock() {
  const [statusFilter, setStatusFilter] = useState<LabelStatus | ''>('')

  const { data: labels = [], isLoading } = useQuery({
    queryKey: ['stock-labels', statusFilter],
    queryFn: () => stockLabelsService.list(statusFilter ? { status: statusFilter } : undefined),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Stock</h1>
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-600">Filter by status:</label>
        <select
          className="rounded border px-2 py-1 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as LabelStatus | '')}
        >
          <option value="">All</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

      <div className="overflow-x-auto rounded-xl border bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th className="px-4 py-3">Progressivo</th>
              <th className="px-4 py-3">Item</th>
              <th className="px-4 py-3">Tons</th>
              <th className="px-4 py-3">Market</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Avg Days Idle</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {labels.map((label: StockLabel) => (
              <tr key={label.progressivo} className="hover:bg-gray-50">
                <td className="px-4 py-2 font-mono">{label.progressivo}</td>
                <td className="px-4 py-2">{label.item_code}</td>
                <td className="px-4 py-2">{label.volume_tons}</td>
                <td className="px-4 py-2">{label.market_type}</td>
                <td className="px-4 py-2">
                  <StatusBadge status={label.status} />
                </td>
                <td className="px-4 py-2">{label.avg_days_idle ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {labels.length === 0 && !isLoading && (
          <p className="px-4 py-6 text-center text-sm text-gray-400">No labels found.</p>
        )}
      </div>
    </div>
  )
}

const STATUS_COLORS: Record<LabelStatus, string> = {
  available: 'bg-green-100 text-green-800',
  reserved: 'bg-yellow-100 text-yellow-800',
  in_transit: 'bg-blue-100 text-blue-800',
  in_shipment: 'bg-purple-100 text-purple-800',
  delivered: 'bg-gray-100 text-gray-600',
  damaged: 'bg-red-100 text-red-800',
}

function StatusBadge({ status }: { status: LabelStatus }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[status]}`}>
      {status}
    </span>
  )
}
