import React, { useState, useEffect } from 'react'
import { ReconstructionRequest } from '../lib/types'

interface SidebarProps {
  mode: 'qty' | 'capital'
  onModeChange: (mode: 'qty' | 'capital') => void
  onSubmit: (request: ReconstructionRequest) => void
  onReset: () => void
  summaryData: { shares: string; price: string; outlay: string } | null
  isLoading: boolean
  error?: string | null
}

export default function Sidebar({
  mode,
  onModeChange,
  onSubmit,
  onReset,
  summaryData,
  isLoading,
  error,
}: SidebarProps) {
  const [ticker, setTicker] = useState('')
  const [exchange, setExchange] = useState<'NSE' | 'BSE'>('NSE')
  const [buyDate, setBuyDate] = useState('')
  const [quantity, setQuantity] = useState('')
  const [capital, setCapital] = useState('')

  // If summaryData becomes null, we want to clear the inputs as well (e.g. on reset)
  useEffect(() => {
    if (!summaryData) {
      setTicker('')
      setExchange('NSE')
      setBuyDate('')
      setQuantity('')
      setCapital('')
    }
  }, [summaryData])

  const handleReset = () => {
    setTicker('')
    setExchange('NSE')
    setBuyDate('')
    setQuantity('')
    setCapital('')
    onReset()
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isLoading) return

    const request: ReconstructionRequest = {
      ticker: ticker.trim().toUpperCase(),
      exchange,
      buy_date: buyDate.trim(),
    }

    if (mode === 'qty') {
      request.quantity = quantity ? parseInt(quantity, 10) : undefined
    } else {
      request.total_amount_invested = capital ? parseFloat(capital) : undefined
    }

    onSubmit(request)
  }

  return (
    <aside className="sw-sidebar">
      <div className="sw-section-title">Parameters</div>
      <form onSubmit={handleSubmit}>
        {/* Mode Selector */}
        <div className="sw-mode-row">
          <button
            type="button"
            className={`sw-mode ${mode === 'qty' ? 'active' : ''}`}
            onClick={() => onModeChange('qty')}
          >
            By Qty
          </button>
          <button
            type="button"
            className={`sw-mode ${mode === 'capital' ? 'active' : ''}`}
            onClick={() => onModeChange('capital')}
          >
            By Capital
          </button>
        </div>

        {/* Ticker Input */}
        <div className="sw-field">
          <label htmlFor="ticker-input">Ticker Symbol</label>
          <input
            id="ticker-input"
            type="text"
            className="sw-input"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="E.G. INFY"
            required
            disabled={isLoading}
          />
        </div>

        {/* Exchange Selector */}
        <div className="sw-field">
          <label htmlFor="exchange-select">Exchange</label>
          <select
            id="exchange-select"
            className="sw-select"
            value={exchange}
            onChange={(e) => setExchange(e.target.value as 'NSE' | 'BSE')}
            disabled={isLoading}
          >
            <option value="NSE">NSE</option>
            <option value="BSE">BSE</option>
          </select>
        </div>

        {/* Buy Date Input */}
        <div className="sw-field">
          <label htmlFor="buy-date-input">Buy Date</label>
          <input
            id="buy-date-input"
            type="text"
            className="sw-input"
            value={buyDate}
            onChange={(e) => setBuyDate(e.target.value)}
            placeholder="YYYY-MM-DD"
            required
            disabled={isLoading}
          />
        </div>

        {/* Dynamic Quantity or Capital Input */}
        <div className="sw-field">
          {mode === 'qty' ? (
            <>
              <label htmlFor="qty-input">Quantity</label>
              <input
                id="qty-input"
                type="number"
                min="1"
                className="sw-input"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="E.G. 100"
                required
                disabled={isLoading}
              />
            </>
          ) : (
            <>
              <label htmlFor="capital-input">Total Invested</label>
              <input
                id="capital-input"
                type="number"
                min="1"
                className="sw-input"
                value={capital}
                onChange={(e) => setCapital(e.target.value)}
                placeholder="E.G. 50000"
                required
                disabled={isLoading}
              />
            </>
          )}
        </div>

        {/* Action Buttons */}
        <div className="sw-btn-row">
          <button
            type="button"
            className="sw-btn"
            onClick={handleReset}
            disabled={isLoading}
          >
            Reset
          </button>
          <button
            type="submit"
            className="sw-btn sw-btn-primary"
            disabled={isLoading}
          >
            {isLoading ? 'RECONSTRUCTING...' : 'Reconstruct →'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-4 p-2.5 border-[1.5px] border-[#d62828] text-[#d62828] font-mono text-[9px] uppercase leading-relaxed break-words">
          {error}
        </div>
      )}

      {/* Summary / Baseline Details Section */}
      {summaryData && (
        <div className="sw-summary">
          <div className="sw-section-title">Baseline Details</div>
          <div className="sw-sum-row">
            <span>Initial Shares</span>
            <strong>{summaryData.shares}</strong>
          </div>
          <div className="sw-sum-row">
            <span>Initial Price</span>
            <strong>{summaryData.price}</strong>
          </div>
          <div className="sw-sum-row">
            <span>Total Outlay</span>
            <strong>{summaryData.outlay}</strong>
          </div>
        </div>
      )}
    </aside>
  )
}
