'use client'

import React, { useState } from 'react'
import Header from '../components/Header'
import Sidebar from '../components/Sidebar'
import MetricsGrid from '../components/MetricsGrid'
import Timeline from '../components/Timeline'
import { ReconstructionRequest, ReconstructionResponse } from '../lib/types'
import { reconstructPortfolio } from '../lib/api'

// Helper function to format Indian Rupee values with a guaranteed symbol prefix
function formatCurrency(valStr: string | number, fractionDigits = 0): string {
  const num = typeof valStr === 'string' ? parseFloat(valStr) : valStr
  if (isNaN(num)) return '₹0'
  const formattedNum = new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits,
  }).format(num)
  return `₹${formattedNum}`
}

export default function Page() {
  const [mode, setMode] = useState<'qty' | 'capital'>('qty')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<ReconstructionResponse | null>(null)

  const handleSubmit = async (request: ReconstructionRequest) => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await reconstructPortfolio(request)
      setResponse(res)
    } catch (err: any) {
      setError(err?.message ?? 'Reconstruction failed')
      setResponse(null)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setResponse(null)
    setError(null)
    setIsLoading(false)
  }

  // Derive metrics and summary data dynamically from the API response
  const metrics = response
    ? {
        currentShares: response.current_state.quantity.toLocaleString('en-IN'),
        multiplier: `${(response.current_state.quantity / response.original_quantity).toFixed(1)}×`,
        costBasis: formatCurrency(response.current_state.adjusted_cost_basis_per_share, 2),
        initialCost: formatCurrency(
          parseFloat(response.original_investment) / response.original_quantity,
          2
        ),
        totalDividends: formatCurrency(response.wealth_summary.total_dividends_received, 0),
        unrealizedValue: formatCurrency(response.wealth_summary.unrealized_gain, 0),
        totalWealth: formatCurrency(response.wealth_summary.total_wealth_if_sold, 0),
        wealthPercent: (() => {
          const initial = parseFloat(response.original_investment)
          const wealth = parseFloat(response.wealth_summary.total_wealth_if_sold)
          const returnsPct = initial > 0 ? ((wealth / initial) - 1) * 100 : 0
          return `${returnsPct >= 0 ? '+' : ''}${Math.round(returnsPct).toLocaleString('en-IN')}%`
        })(),
        cagr: (() => {
          const buyDateObj = new Date(response.buy_date)
          const today = new Date()
          const diffTime = Math.abs(today.getTime() - buyDateObj.getTime())
          const holdingYears = diffTime / (1000 * 60 * 60 * 24 * 365.25)
          const marketValue = parseFloat(response.current_state.current_market_value)
          const initial = parseFloat(response.original_investment)
          const cagrVal = (Math.pow(marketValue / initial, 1 / holdingYears) - 1) * 100
          return `${cagrVal.toFixed(1)}%`
        })(),
        yearsHeld: (() => {
          const buyDateObj = new Date(response.buy_date)
          const today = new Date()
          const diffTime = Math.abs(today.getTime() - buyDateObj.getTime())
          const holdingYears = diffTime / (1000 * 60 * 60 * 24 * 365.25)
          return `${holdingYears.toFixed(1)} years`
        })(),
      }
    : null

  const summaryData = response
    ? {
        shares: response.original_quantity.toLocaleString('en-IN'),
        price: formatCurrency(
          parseFloat(response.original_investment) / response.original_quantity,
          2
        ),
        outlay: formatCurrency(response.original_investment, 2),
      }
    : null

  return (
    <div className="sw-root min-h-screen">
      <Header />
      <div className="sw-body min-h-[calc(100vh-62px)]">
        <Sidebar
          mode={mode}
          onModeChange={setMode}
          onSubmit={handleSubmit}
          onReset={handleReset}
          summaryData={summaryData}
          isLoading={isLoading}
          error={error}
        />
        <main className="sw-main">
          {isLoading ? (
            <div className="text-xl font-bold tracking-widest text-[#111] text-center mt-12 font-mono">
              RECONSTRUCTING...
            </div>
          ) : response && metrics ? (
            <>
              <MetricsGrid {...metrics} />
              <Timeline events={response.timeline} />
            </>
          ) : (
            <div className="flex flex-col items-center justify-center border-[1.5px] border-[#111] p-12 bg-white text-[#555] font-mono text-[10px] tracking-wider uppercase text-center h-[300px]">
              <div className="font-bold text-[#111] text-xs mb-2">READY TO RECONSTRUCT</div>
              <div>ENTER PARAMETERS AND CLICK RECONSTRUCT TO VIEW PORTFOLIO HISTORY.</div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
