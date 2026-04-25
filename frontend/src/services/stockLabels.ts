import { api } from './api'
import type { StockLabel, LabelStatus } from '../types'

export const stockLabelsService = {
  list: (params?: { status?: LabelStatus; market_type?: string }) =>
    api.get<StockLabel[]>('/stock-labels', { params }).then((r) => r.data),

  get: (progressivo: string) =>
    api.get<StockLabel>(`/stock-labels/${progressivo}`).then((r) => r.data),

  updateStatus: (progressivo: string, new_status: LabelStatus) =>
    api.patch<StockLabel>(`/stock-labels/${progressivo}/status`, { new_status }).then((r) => r.data),

  updateLocation: (progressivo: string, location_id: string) =>
    api.patch<StockLabel>(`/stock-labels/${progressivo}/location`, { location_id }).then((r) => r.data),
}
