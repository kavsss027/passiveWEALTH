import React from 'react'
import { TimelineEvent as TimelineEventType } from '../lib/types'

interface TimelineEventProps {
  event: TimelineEventType
  isLast: boolean
}

const STRIPE_COLORS = {
  BUY: '#3b82f6',
  SPLIT: '#8b5cf6',
  DIVIDEND: '#10b981',
  BONUS: '#ec4899',
}

function formatCurrency(valueStr: string): string {
  const num = parseFloat(valueStr)
  if (isNaN(num)) return valueStr
  if (num === 0) return '₹0.00'
  const formattedNum = new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num)
  return `₹${formattedNum}`
}

export default function TimelineEvent({ event, isLast }: TimelineEventProps) {
  const color = STRIPE_COLORS[event.event_type] || '#111111'

  // Format the meta text in JetBrains Mono style
  const sharesText = `SHARES: ${event.quantity_before} → ${event.quantity_after}`
  const impactVal = parseFloat(event.financial_impact)
  const impactText = impactVal !== 0 ? ` | IMPACT: ${formatCurrency(event.financial_impact)}` : ''
  const divVal = parseFloat(event.cumulative_dividends)
  const divText = divVal !== 0 ? ` | CUMULATIVE DIV: ${formatCurrency(event.cumulative_dividends)}` : ''

  const metaString = `${event.event_date} | ${sharesText}${impactText}${divText}`

  return (
    <div
      className="sw-event"
      style={isLast ? { borderBottom: 'none' } : undefined}
    >
      {/* Event Stripe */}
      <div
        className="sw-event-stripe"
        style={{ backgroundColor: color }}
      />
      {/* Event Body */}
      <div className="sw-event-body">
        <div>
          <div className="sw-event-title">{event.description}</div>
          <div className="sw-event-meta">{metaString}</div>
        </div>
        {/* Badge */}
        <span
          className="sw-badge"
          style={{ borderColor: color, color: color }}
        >
          {event.event_type}
        </span>
      </div>
    </div>
  )
}
