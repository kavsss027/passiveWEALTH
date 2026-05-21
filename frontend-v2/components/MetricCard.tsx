import React from 'react'

interface MetricCardProps {
  label: string
  value: string
  sub: string
  accentColor: string
  valueColor?: string
  topBorder?: boolean
}

export default function MetricCard({
  label,
  value,
  sub,
  accentColor,
  valueColor,
  topBorder,
}: MetricCardProps) {
  // Construct dynamic class names based on topBorder.
  // The base right border is handled by .sw-metric, which we override for the last card in each row.
  const isLastInRow = label === 'TOTAL DIVIDENDS' || label === 'CAGR'

  return (
    <div
      className={`sw-metric ${topBorder ? 'border-t-[1.5px] border-t-[#111]' : ''}`}
      style={isLastInRow ? { borderRight: 'none' } : undefined}
    >
      <div
        className="sw-metric-accent"
        style={{ backgroundColor: accentColor }}
      />
      <div className="sw-metric-label">{label}</div>
      <div
        className="sw-metric-val"
        style={valueColor ? { color: valueColor } : undefined}
      >
        {value}
      </div>
      <div className="sw-metric-sub">{sub}</div>
    </div>
  )
}
