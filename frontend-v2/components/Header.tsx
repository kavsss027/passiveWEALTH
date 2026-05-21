import React from 'react'

export default function Header() {
  return (
    <header className="sw-header">
      <div className="sw-logo">
        PassiveWEALTH
        <span>Long-term wealth reconstruction</span>
      </div>
      <nav className="sw-nav">
        <div className="sw-nav-item active">Dashboard</div>
        <div className="sw-nav-item">History</div>
        <div className="sw-nav-item">Export</div>
      </nav>
    </header>
  )
}
