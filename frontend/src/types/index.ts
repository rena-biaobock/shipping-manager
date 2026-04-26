export type MarketType = 'MI' | 'ME'

export type LabelStatus =
  | 'available'
  | 'reserved'
  | 'in_transit'
  | 'in_shipment'
  | 'delivered'
  | 'damaged'

export type ShipmentStatus =
  | 'draft'
  | 'confirmed'
  | 'loading'
  | 'dispatched'
  | 'delivered'
  | 'cancelled'

export interface StockLabel {
  progressivo: string
  item_code: string
  description: string
  customer_item_ref: string | null
  actual_length_m: string | null
  market_type: MarketType
  volume_tons: string
  piece_count: number
  status: LabelStatus
  order_number: string | null
  order_condition: string | null
  country: string | null
  exit_date: string | null
  embarque_id: string | null
  avg_days_idle: number | null
  is_standard_bundle: boolean | null
  location_id: string | null
}

export interface Truck {
  id: string
  name: string
  plate: string | null
  max_weight_tons: string
  active: boolean
}

export interface TruckCreate {
  name: string
  plate?: string
  max_weight_tons: number
}

export interface Shipment {
  id: string
  truck_id: string | null
  order_id: string | null
  status: ShipmentStatus
  destination: string | null
  customer: string | null
  country: string | null
  market_type: MarketType | null
  notes: string | null
  total_weight_tons: string | null
  scheduled_at: string | null
  dispatched_at: string | null
  delivered_at: string | null
}

export interface ShipmentCreate {
  truck_id: string
  destination?: string
  customer?: string
  country?: string
  market_type?: MarketType
  notes?: string
}

export interface LoadPlanItem {
  progressivo: string
  volume_tons: number
}

export interface LoadPlan {
  items: LoadPlanItem[]
  total_weight_tons: number
  partial: boolean
}

export interface PackingFilters {
  country?: string
  order_condition?: string
  exit_date_from?: string
  exit_date_to?: string
}
