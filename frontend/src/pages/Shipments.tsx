import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { shipmentsService } from '../services/shipments'
import { trucksService } from '../services/trucks'
import type { Shipment, ShipmentStatus } from '../types'

const schema = z.object({
  truck_id: z.string().min(1, 'Select a truck'),
  destination: z.string().optional(),
  customer: z.string().optional(),
})
type FormValues = z.infer<typeof schema>

export default function Shipments() {
  const queryClient = useQueryClient()

  const { data: shipments = [], isLoading } = useQuery({
    queryKey: ['shipments'],
    queryFn: () => shipmentsService.list(),
  })
  const { data: trucks = [] } = useQuery({
    queryKey: ['trucks'],
    queryFn: () => trucksService.list(),
  })

  const createMutation = useMutation({
    mutationFn: shipmentsService.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['shipments'] }),
  })
  const statusMutation = useMutation({
    mutationFn: ({ id, new_status }: { id: string; new_status: ShipmentStatus }) =>
      shipmentsService.updateStatus(id, new_status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['shipments'] }),
  })

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = (data: FormValues) => {
    createMutation.mutate(data, { onSuccess: () => reset() })
  }

  const nextStatus: Partial<Record<ShipmentStatus, ShipmentStatus>> = {
    draft: 'confirmed',
    confirmed: 'loading',
    loading: 'dispatched',
    dispatched: 'delivered',
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Shipments</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-wrap gap-3 rounded-xl border bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-1">
          <select {...register('truck_id')} className="rounded border px-2 py-1 text-sm">
            <option value="">Select truck…</option>
            {trucks.map((t) => (
              <option key={t.id} value={t.id}>{t.name} ({t.max_weight_tons} t)</option>
            ))}
          </select>
          {errors.truck_id && <span className="text-xs text-red-500">{errors.truck_id.message}</span>}
        </div>
        <input {...register('destination')} placeholder="Destination" className="rounded border px-2 py-1 text-sm" />
        <input {...register('customer')} placeholder="Customer" className="rounded border px-2 py-1 text-sm" />
        <button type="submit" className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700">
          Create Shipment
        </button>
      </form>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

      <div className="space-y-3">
        {shipments.map((s: Shipment) => {
          const advance = nextStatus[s.status]
          return (
            <div key={s.id} className="rounded-xl border bg-white p-4 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-mono text-xs text-gray-400">{s.id}</p>
                  <p className="mt-0.5 font-semibold">{s.destination ?? '—'}</p>
                  {s.customer && <p className="text-sm text-gray-500">{s.customer}</p>}
                  {s.total_weight_tons && (
                    <p className="mt-1 text-sm">Weight: <span className="font-medium">{s.total_weight_tons} t</span></p>
                  )}
                </div>
                <div className="flex flex-col items-end gap-2">
                  <StatusBadge status={s.status} />
                  {advance && (
                    <button
                      onClick={() => statusMutation.mutate({ id: s.id, new_status: advance })}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      → {advance}
                    </button>
                  )}
                  {(s.status === 'draft' || s.status === 'confirmed') && (
                    <button
                      onClick={() => statusMutation.mutate({ id: s.id, new_status: 'cancelled' })}
                      className="text-xs text-red-500 hover:underline"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

const STATUS_COLORS: Record<ShipmentStatus, string> = {
  draft: 'bg-gray-100 text-gray-600',
  confirmed: 'bg-blue-100 text-blue-800',
  loading: 'bg-yellow-100 text-yellow-800',
  dispatched: 'bg-purple-100 text-purple-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

function StatusBadge({ status }: { status: ShipmentStatus }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[status]}`}>
      {status}
    </span>
  )
}
