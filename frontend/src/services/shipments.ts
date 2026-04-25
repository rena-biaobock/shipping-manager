import { api } from './api'
import type { Shipment, ShipmentCreate, ShipmentStatus, LoadPlan, PackingFilters } from '../types'

export const shipmentsService = {
  list: (status?: ShipmentStatus) =>
    api.get<Shipment[]>('/shipments', { params: status ? { status } : undefined }).then((r) => r.data),

  get: (id: string) => api.get<Shipment>(`/shipments/${id}`).then((r) => r.data),

  create: (body: ShipmentCreate) => api.post<Shipment>('/shipments', body).then((r) => r.data),

  updateStatus: (id: string, new_status: ShipmentStatus) =>
    api.patch<Shipment>(`/shipments/${id}/status`, { new_status }).then((r) => r.data),

  addLabels: (id: string, progressivos: string[]) =>
    api.post(`/shipments/${id}/labels`, { progressivos }).then((r) => r.data),

  removeLabels: (id: string) => api.delete(`/shipments/${id}/labels`).then((r) => r.data),
}

export const binPackingService = {
  pack: (truck_id: string, filters: PackingFilters = {}, max_iterations?: number) =>
    api.post<LoadPlan>('/bin-packing/pack', { truck_id, filters, max_iterations }).then((r) => r.data),
}
