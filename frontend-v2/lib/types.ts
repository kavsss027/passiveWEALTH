export interface ReconstructionRequest {
  ticker: string
  exchange: 'NSE' | 'BSE'
  buy_date: string
  quantity?: number
  total_amount_invested?: number
}

export interface CurrentState {
  quantity: number
  current_price_per_share: string
  current_market_value: string
  adjusted_cost_basis_per_share: string
  total_invested: string
}

export interface WealthSummary {
  total_dividends_received: string
  unrealized_gain: string
  unrealized_gain_label: string
  total_wealth_if_sold: string
  wealth_multiple: string
}

export type EventType = 'BUY' | 'SPLIT' | 'BONUS' | 'DIVIDEND'
export type ImpactType = 'INVESTED' | 'STRUCTURAL' | 'REALIZED' | 'UNREALIZED'

export interface TimelineEvent {
  event_date: string
  event_type: EventType
  description: string
  quantity_before: number
  quantity_after: number
  financial_impact: string
  impact_type: ImpactType
  cumulative_dividends: string
}

export interface DataQuality {
  confidence: 'HIGH' | 'MEDIUM' | 'LOW'
  sources_used: string[]
  warnings: string[]
}

export interface ReconstructionResponse {
  ticker: string
  exchange: string
  buy_date: string
  original_quantity: number
  original_investment: string
  current_state: CurrentState
  wealth_summary: WealthSummary
  timeline: TimelineEvent[]
  data_quality: DataQuality
}
