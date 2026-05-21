import React from 'react'
import MetricCard from './MetricCard'

interface MetricsGridProps {
  currentShares: string
  multiplier: string
  costBasis: string
  initialCost: string
  totalDividends: string
  unrealizedValue: string
  totalWealth: string
  wealthPercent: string
  cagr: string
  yearsHeld: string
}

export default function MetricsGrid({
  currentShares,
  multiplier,
  costBasis,
  initialCost,
  totalDividends,
  unrealizedValue,
  totalWealth,
  wealthPercent,
  cagr,
  yearsHeld,
}: MetricsGridProps) {
  return (
    <div className="sw-metrics">
      {/* Row 1 */}
      <MetricCard
        label="CURRENT SHARES"
        value={currentShares}
        sub={`${multiplier} Multiplier`}
        accentColor="#d62828"
      />
      <MetricCard
        label="ADJ. COST BASIS"
        value={costBasis}
        sub={`Initial: ${initialCost}`}
        accentColor="#d62828"
      />
      <MetricCard
        label="TOTAL DIVIDENDS"
        value={totalDividends}
        sub="Received in Bank"
        accentColor="#10b981"
        valueColor="#10b981"
      />

      {/* Row 2 */}
      <MetricCard
        label="UNREALIZED VALUE"
        value={unrealizedValue}
        sub="Current Market Value"
        accentColor="#f59e0b"
        topBorder={true}
      />
      <MetricCard
        label="TOTAL WEALTH"
        value={totalWealth}
        sub={wealthPercent}
        accentColor="#ec4899"
        topBorder={true}
      />
      <MetricCard
        label="CAGR"
        value={cagr}
        sub={`Held: ${yearsHeld}`}
        accentColor="#a855f7"
        topBorder={true}
      />
    </div>
  )
}
