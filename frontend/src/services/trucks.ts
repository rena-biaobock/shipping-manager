import { api } from './api'
import type { Truck, TruckCreate } from '../types'

export const trucksService = {
  list: () => api.get<Truck[]>('/trucks').then((r) => r.data),
  get: (id: string) => api.get<Truck>(`/trucks/${id}`).then((r) => r.data),
  create: (body: TruckCreate) => api.post<Truck>('/trucks', body).then((r) => r.data),
  deactivate: (id: string) => api.delete(`/trucks/${id}`),
}
