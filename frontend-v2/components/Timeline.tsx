import React, { useState } from 'react'
import { TimelineEvent as TimelineEventType } from '../lib/types'
import TimelineEvent from './TimelineEvent'

interface TimelineProps {
  events: TimelineEventType[]
}

type TabType = 'ALL' | 'SPLIT' | 'BONUS' | 'DIVIDEND'

export default function Timeline({ events = [] }: TimelineProps) {
  const [activeTab, setActiveTab] = useState<TabType>('ALL')

  // Filter events based on the active tab
  const filteredEvents = events.filter((event) => {
    if (activeTab === 'ALL') return true
    return event.event_type === activeTab
  })

  return (
    <div className="sw-timeline">
      {/* Timeline Header */}
      <div className="sw-tl-head">
        <div className="sw-tl-title">WEALTH & ACTIONS TIMELINE</div>
        <div className="sw-tl-tabs">
          <button
            onClick={() => setActiveTab('ALL')}
            className={`sw-tl-tab ${activeTab === 'ALL' ? 'active' : ''}`}
          >
            All Events
          </button>
          <button
            onClick={() => setActiveTab('SPLIT')}
            className={`sw-tl-tab ${activeTab === 'SPLIT' ? 'active' : ''}`}
          >
            Splits
          </button>
          <button
            onClick={() => setActiveTab('BONUS')}
            className={`sw-tl-tab ${activeTab === 'BONUS' ? 'active' : ''}`}
          >
            Bonus
          </button>
          <button
            onClick={() => setActiveTab('DIVIDEND')}
            className={`sw-tl-tab ${activeTab === 'DIVIDEND' ? 'active' : ''}`}
          >
            Dividends
          </button>
        </div>
      </div>

      {/* Events List */}
      <div className="bg-white">
        {filteredEvents.length === 0 ? (
          <div className="p-4 text-xs font-mono text-center text-[#888]">
            NO EVENTS FOUND FOR THIS FILTER
          </div>
        ) : (
          filteredEvents.map((event, index) => (
            <TimelineEvent
              key={`${event.event_date}-${event.event_type}-${index}`}
              event={event}
              isLast={index === filteredEvents.length - 1}
            />
          ))
        )}
      </div>
    </div>
  )
}
