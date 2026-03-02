import React from 'react'
import './MatchResults.css'

const MatchResults = ({ results, onViewDetails, onNewSearch }) => {
  const { matches = [], total_trials_considered = 0, hard_filtered_count = 0, processing_time_ms = 0 } = results

  const formatProcessingTime = (ms) => {
    return (ms / 1000).toFixed(1)
  }

  return (
    <div className="match-results">
      <div className="results-header">
        <h1>Your Clinical Trial Matches</h1>
        <button 
          className="new-search-button"
          onClick={onNewSearch}
          aria-label="Start a new search"
        >
          New Search
        </button>
      </div>

      <div className="results-summary">
        <div className="summary-card">
          <div className="summary-icon">🔍</div>
          <div className="summary-content">
            <div className="summary-value">{total_trials_considered.toLocaleString()}</div>
            <div className="summary-label">Trials Searched</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">✓</div>
          <div className="summary-content">
            <div className="summary-value">{matches.length}</div>
            <div className="summary-label">Best Matches Found</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">⚡</div>
          <div className="summary-content">
            <div className="summary-value">{formatProcessingTime(processing_time_ms)}s</div>
            <div className="summary-label">Processing Time</div>
          </div>
        </div>
      </div>

      {matches.length === 0 ? (
        <div className="no-results">
          <div className="no-results-icon">😔</div>
          <h2>No Matches Found</h2>
          <p>We couldn't find any clinical trials matching your profile at this time.</p>
          <p>Try adjusting your search criteria or check back later for new trials.</p>
          <button className="primary-button" onClick={onNewSearch}>
            Try Another Search
          </button>
        </div>
      ) : (
        <div className="matches-list">
          <h2>Top {matches.length} Matches</h2>
          {matches.map((match, index) => (
            <TrialMatchCard 
              key={match.trial_id || index}
              match={match}
              rank={index + 1}
              onViewDetails={onViewDetails}
            />
          ))}
        </div>
      )}
    </div>
  )
}

const TrialMatchCard = ({ match, rank, onViewDetails }) => {
  const {
    trial_id,
    title,
    match_score,
    explanation,
    key_criteria = [],
    location = 'Location not specified'
  } = match

  const matchPercentage = Math.round(match_score * 100)

  const getMatchClass = (percentage) => {
    if (percentage >= 85) return 'excellent'
    if (percentage >= 70) return 'good'
    return 'fair'
  }

  const parseCriterion = (criterion) => {
    const isPositive = criterion.startsWith('✅')
    const isWarning = criterion.startsWith('⚠️')
    const text = criterion.replace(/^[✅⚠️]\s*/, '')
    
    return {
      isPositive,
      isWarning,
      text
    }
  }

  return (
    <article className={`trial-match-card ${getMatchClass(matchPercentage)}`}>
      <div className="card-header">
        <div className="match-badge">
          <div className="match-percentage">{matchPercentage}%</div>
          <div className="match-label">Match</div>
        </div>
        <div className="trial-info">
          <div className="trial-rank">#{rank}</div>
          <h3 className="trial-title">{title}</h3>
          <div className="trial-location">
            <span className="location-icon" aria-hidden="true">📍</span>
            {location}
          </div>
        </div>
      </div>

      {explanation && (
        <div className="match-explanation">
          <p>{explanation}</p>
        </div>
      )}

      {key_criteria.length > 0 && (
        <div className="key-criteria">
          <h4>Key Eligibility Criteria</h4>
          <ul className="criteria-list">
            {key_criteria.map((criterion, index) => {
              const parsed = parseCriterion(criterion)
              return (
                <li 
                  key={index}
                  className={`criterion ${parsed.isPositive ? 'positive' : ''} ${parsed.isWarning ? 'warning' : ''}`}
                >
                  <span className="criterion-icon" aria-hidden="true">
                    {parsed.isPositive ? '✅' : parsed.isWarning ? '⚠️' : '•'}
                  </span>
                  <span className="criterion-text">{parsed.text}</span>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      <div className="card-actions">
        <button 
          className="view-details-button"
          onClick={() => onViewDetails(match)}
          aria-label={`View full details for ${title}`}
        >
          View Full Details
        </button>
      </div>
    </article>
  )
}

export default MatchResults
