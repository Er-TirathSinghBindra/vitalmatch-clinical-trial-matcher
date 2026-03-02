import React, { useState, useEffect } from 'react'
import './ProcessingIndicator.css'

const PROCESSING_STAGES = [
  { id: 'searching', label: 'Searching Trials', duration: 3000 },
  { id: 'filtering', label: 'Filtering by Criteria', duration: 4000 },
  { id: 'analyzing', label: 'AI Analysis', duration: 6000 }
]

const ProcessingIndicator = ({ onCancel }) => {
  const [currentStage, setCurrentStage] = useState(0)
  const [progress, setProgress] = useState(0)
  const [trialCounts, setTrialCounts] = useState({
    searching: 0,
    filtering: 0,
    analyzing: 0
  })
  const [elapsedTime, setElapsedTime] = useState(0)

  useEffect(() => {
    // Simulate trial counts
    const countInterval = setInterval(() => {
      setTrialCounts(prev => {
        if (currentStage === 0) {
          return { ...prev, searching: Math.min(prev.searching + 50, 1247) }
        } else if (currentStage === 1) {
          return { ...prev, filtering: Math.min(prev.filtering + 5, 43) }
        } else if (currentStage === 2) {
          return { ...prev, analyzing: Math.min(prev.analyzing + 1, 5) }
        }
        return prev
      })
    }, 200)

    return () => clearInterval(countInterval)
  }, [currentStage])

  useEffect(() => {
    // Track elapsed time
    const timeInterval = setInterval(() => {
      setElapsedTime(prev => prev + 1)
    }, 1000)

    return () => clearInterval(timeInterval)
  }, [])

  useEffect(() => {
    // Progress through stages
    const totalDuration = PROCESSING_STAGES.reduce((sum, stage) => sum + stage.duration, 0)
    let elapsed = 0

    const progressInterval = setInterval(() => {
      elapsed += 100
      const newProgress = Math.min((elapsed / totalDuration) * 100, 100)
      setProgress(newProgress)

      // Update current stage
      let cumulativeDuration = 0
      for (let i = 0; i < PROCESSING_STAGES.length; i++) {
        cumulativeDuration += PROCESSING_STAGES[i].duration
        if (elapsed < cumulativeDuration) {
          setCurrentStage(i)
          break
        }
      }

      if (elapsed >= totalDuration) {
        clearInterval(progressInterval)
      }
    }, 100)

    return () => clearInterval(progressInterval)
  }, [])

  const estimatedTimeRemaining = Math.max(0, 15 - elapsedTime)

  return (
    <div className="processing-indicator" role="status" aria-live="polite">
      <div className="processing-header">
        <h2>Finding Your Matches</h2>
        <p>This usually takes 10-15 seconds</p>
      </div>

      <div className="progress-container">
        <div 
          className="progress-bar" 
          role="progressbar"
          aria-valuenow={Math.round(progress)}
          aria-valuemin="0"
          aria-valuemax="100"
          aria-label={`Processing: ${Math.round(progress)}% complete`}
        >
          <div 
            className="progress-fill" 
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="progress-percentage">
          {Math.round(progress)}%
        </div>
      </div>

      <div className="processing-stages">
        {PROCESSING_STAGES.map((stage, index) => (
          <div 
            key={stage.id}
            className={`stage ${index === currentStage ? 'active' : ''} ${index < currentStage ? 'completed' : ''}`}
          >
            <div className="stage-icon">
              {index < currentStage ? (
                <span className="checkmark" aria-label="completed">✓</span>
              ) : index === currentStage ? (
                <span className="spinner" aria-label="in progress">⟳</span>
              ) : (
                <span className="pending" aria-label="pending">○</span>
              )}
            </div>
            <div className="stage-content">
              <div className="stage-label">{stage.label}</div>
              {index <= currentStage && (
                <div className="stage-count" aria-live="polite">
                  {index === 0 && `${trialCounts.searching} trials found`}
                  {index === 1 && `${trialCounts.filtering} candidates`}
                  {index === 2 && `${trialCounts.analyzing} best matches`}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="processing-info">
        <div className="time-info">
          <span className="time-label">Elapsed:</span>
          <span className="time-value">{elapsedTime}s</span>
        </div>
        <div className="time-info">
          <span className="time-label">Estimated remaining:</span>
          <span className="time-value">{estimatedTimeRemaining}s</span>
        </div>
      </div>

      {onCancel && (
        <div className="processing-actions">
          <button 
            className="cancel-button" 
            onClick={onCancel}
            aria-label="Cancel search"
          >
            Cancel Search
          </button>
        </div>
      )}
    </div>
  )
}

export default ProcessingIndicator
