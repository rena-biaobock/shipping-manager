import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { trucksService } from '../services/trucks'
import type { Truck } from '../types'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  plate: z.string().optional(),
  max_weight_tons: z.number().positive('Must be positive'),
})
type FormValues = z.infer<typeof schema>

export default function Trucks() {
  const queryClient = useQueryClient()
  const { data: trucks = [], isLoading } = useQuery({
    queryKey: ['trucks'],
    queryFn: () => trucksService.list(),
  })

  const createMutation = useMutation({
    mutationFn: trucksService.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trucks'] }),
  })

  const deactivateMutation = useMutation({
    mutationFn: trucksService.deactivate,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trucks'] }),
  })

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = (data: FormValues) => {
    createMutation.mutate(data, { onSuccess: () => reset() })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Trucks</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-wrap gap-3 rounded-xl border bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-1">
          <input {...register('name')} placeholder="Name" className="rounded border px-2 py-1 text-sm" />
          {errors.name && <span className="text-xs text-red-500">{errors.name.message}</span>}
        </div>
        <input {...register('plate')} placeholder="Plate (optional)" className="rounded border px-2 py-1 text-sm" />
        <div className="flex flex-col gap-1">
          <input {...register('max_weight_tons', { valueAsNumber: true })} placeholder="Max weight (t)" type="number" step="0.001"
            className="rounded border px-2 py-1 text-sm w-36" />
          {errors.max_weight_tons && <span className="text-xs text-red-500">{errors.max_weight_tons.message}</span>}
        </div>
        <button type="submit" className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700">
          Add Truck
        </button>
      </form>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {trucks.map((truck: Truck) => (
          <div key={truck.id} className="rounded-xl border bg-white p-4 shadow-sm">
            <p className="font-semibold">{truck.name}</p>
            {truck.plate && <p className="text-sm text-gray-500">{truck.plate}</p>}
            <p className="mt-1 text-sm">Capacity: <span className="font-medium">{truck.max_weight_tons} t</span></p>
            <button
              onClick={() => deactivateMutation.mutate(truck.id)}
              className="mt-3 text-xs text-red-500 hover:underline"
            >
              Deactivate
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
