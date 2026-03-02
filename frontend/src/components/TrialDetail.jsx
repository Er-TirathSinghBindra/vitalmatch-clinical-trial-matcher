import React, { useState, useEffect } from 'react'
import './TrialDetail.css'

const TrialDetail = ({ trial, onBack }) => {
  const [isSaved, setIsSaved] = useState(false)

  useEffect(() => {
    // Check if trial is already saved
    const savedTrials = JSON.parse(localStorage.getItem('savedTrials') || '[]')
    setIsSaved(savedTrials.some(t => t.trial_id === trial.trial_id))
  }, [trial.trial_id])

  const handleSave = () => {
    const savedTrials = JSON.parse(localStorage.getItem('savedTrials') || '[]')
    
    if (isSaved) {
      // Remove from saved
      const updated = savedTrials.filter(t => t.trial_id !== trial.trial_id)
      localStorage.setItem('savedTrials', JSON.stringify(updated))
      setIsSaved(false)
    } else {
      // Add to saved
      savedTrials.push({
        trial_id: trial.trial_id,
        title: trial.title,
        match_score: trial.match_score,
        savedAt: new Date().toISOString()
      })
      localStorage.setItem('savedTrials', JSON.stringify(savedTrials))
      setIsSaved(true)
    }
  }

  const matchPercentage = Math.round(trial.match_score * 100)

  return (
    <div className="trial-detail">
      <div className="detail-header">
        <button 
          className="back-button"
          onClick={onBack}
          aria-label="Back to results"
        >
          ← Back to Results
        </button>
        <button 
          className={`save-button ${isSaved ? 'saved' : ''}`}
          onClick={handleSave}
          aria-label={isSaved ? 'Remove from saved trials' : 'Save trial for later'}
        >
          {isSaved ? '★ Saved' : '☆ Save Trial'}
        </button>
      </div>

      <div className="detail-content">
        <div className="trial-header-section">
          <div className="match-score-large">
            <div className="score-circle">
              <div className="score-value">{matchPercentage}%</div>
              <div className="score-label">Match</div>
            </div>
          </div>
          <div className="trial-title-section">
            <h1>{trial.title}</h1>
            {trial.trial_id && (
              <div className="trial-id">Trial ID: {trial.trial_id}</div>
            )}
            {trial.location && (
              <div className="trial-location">
                <span className="location-icon" aria-hidden="true">📍</span>
                {trial.location}
              </div>
            )}
          </div>
        </div>

        {trial.explanation && (
          <section className="why-matches-section">
            <h2>Why This Matches You</h2>
            <div className="explanation-box">
              <p>{trial.explanation}</p>
            </div>
          </section>
        )}

        {trial.key_criteria && trial.key_criteria.length > 0 && (
          <section className="eligibility-section">
            <h2>Eligibility Criteria Match</h2>
            <div className="criteria-grid">
              {trial.key_criteria.map((criterion, index) => {
                const isPositive = criterion.startsWith('✅')
                const isWarning = criterion.startsWith('⚠️')
                const text = criterion.replace(/^[✅⚠️]\s*/, '')
                
                return (
                  <div 
                    key={index}
                    className={`criterion-card ${isPositive ? 'positive' : ''} ${isWarning ? 'warning' : ''}`}
                  >
                    <div className="criterion-icon">
                      {isPositive ? '✅' : isWarning ? '⚠️' : '•'}
                    </div>
                    <div className="criterion-text">{text}</div>
                  </div>
                )
              })}
            </div>
          </section>
        )}

        {trial.description && (
          <section className="description-section">
            <h2>Trial Description</h2>
            <div className="description-content">
              <p>{trial.description}</p>
            </div>
          </section>
        )}

        {trial.inclusion_text && (
          <section className="requirements-section">
            <h2>Inclusion Criteria</h2>
            <div className="requirements-content">
              <p>{trial.inclusion_text}</p>
            </div>
          </section>
        )}

        {trial.exclusion_text && (
          <section className="requirements-section">
            <h2>Exclusion Criteria</h2>
            <div className="requirements-content exclusion">
              <p>{trial.exclusion_text}</p>
            </div>
          </section>
        )}

        <section className="contact-section">
          <h2>Next Steps</h2>
          <div className="contact-box">
            <div className="contact-info">
              <h3>How to Participate</h3>
              <ol>
                <li>Discuss this trial with your healthcare provider</li>
                <li>Contact the trial site to verify eligibility</li>
                <li>Schedule a screening appointment if eligible</li>
                <li>Review and sign informed consent documents</li>
              </ol>
            </div>
            
            {trial.contact_info ? (
              <div className="contact-details">
                <h3>Contact Information</h3>
                <p>{trial.contact_info}</p>
              </div>
            ) : (
              <div className="contact-details">
                <h3>Find Contact Information</h3>
                <p>
                  Visit{' '}
                  <a 
                    href={`https://clinicaltrials.gov/study/${trial.trial_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="external-link"
                  >
                    ClinicalTrials.gov
                  </a>
                  {' '}for complete contact information and study details.
                </p>
              </div>
            )}
          </div>
        </section>

        <div className="detail-actions">
          <button className="primary-button" onClick={onBack}>
            Back to Results
          </button>
          <button 
            className={`secondary-button ${isSaved ? 'saved' : ''}`}
            onClick={handleSave}
          >
            {isSaved ? '★ Saved' : '☆ Save for Later'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default TrialDetail
