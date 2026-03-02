import React, { useState } from 'react'
import PatientProfileForm from './components/PatientProfileForm'
import ProcessingIndicator from './components/ProcessingIndicator'
import MatchResults from './components/MatchResults'
import TrialDetail from './components/TrialDetail'
import ErrorBoundary from './components/ErrorBoundary'
import { matchTrials } from './api/client'
import './App.css'

const APP_STATES = {
  FORM: 'form',
  PROCESSING: 'processing',
  RESULTS: 'results',
  DETAIL: 'detail',
  ERROR: 'error'
}

function App() {
  const [appState, setAppState] = useState(APP_STATES.FORM)
  const [matchResults, setMatchResults] = useState(null)
  const [selectedTrial, setSelectedTrial] = useState(null)
  const [error, setError] = useState(null)

  const handleFormSubmit = async (patientProfile) => {
    setAppState(APP_STATES.PROCESSING)
    setError(null)

    try {
      // Call API to match trials
      const results = await matchTrials(patientProfile)
      
      setMatchResults(results)
      setAppState(APP_STATES.RESULTS)
    } catch (err) {
      console.error('Error matching trials:', err)
      setError(err.message || 'An unexpected error occurred. Please try again.')
      setAppState(APP_STATES.ERROR)
    }
  }

  const handleCancelSearch = () => {
    setAppState(APP_STATES.FORM)
    setMatchResults(null)
    setError(null)
  }

  const handleViewDetails = (trial) => {
    setSelectedTrial(trial)
    setAppState(APP_STATES.DETAIL)
  }

  const handleBackToResults = () => {
    setAppState(APP_STATES.RESULTS)
    setSelectedTrial(null)
  }

  const handleNewSearch = () => {
    setAppState(APP_STATES.FORM)
    setMatchResults(null)
    setSelectedTrial(null)
    setError(null)
  }

  return (
    <ErrorBoundary>
      <div className="app">
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>

        <header className="app-header">
          <div className="header-content">
            <div className="logo">
              <h1>VitalMatch</h1>
              <p className="tagline">Clinical Trial Matcher</p>
            </div>
            {appState !== APP_STATES.FORM && (
              <button 
                className="home-button"
                onClick={handleNewSearch}
                aria-label="Return to home"
              >
                Home
              </button>
            )}
          </div>
        </header>

        <main id="main-content" className="app-main">
          {appState === APP_STATES.FORM && (
            <PatientProfileForm 
              onSubmit={handleFormSubmit}
              isLoading={false}
            />
          )}

          {appState === APP_STATES.PROCESSING && (
            <ProcessingIndicator onCancel={handleCancelSearch} />
          )}

          {appState === APP_STATES.RESULTS && matchResults && (
            <MatchResults 
              results={matchResults}
              onViewDetails={handleViewDetails}
              onNewSearch={handleNewSearch}
            />
          )}

          {appState === APP_STATES.DETAIL && selectedTrial && (
            <TrialDetail 
              trial={selectedTrial}
              onBack={handleBackToResults}
            />
          )}

          {appState === APP_STATES.ERROR && (
            <div className="error-container">
              <div className="error-icon">⚠️</div>
              <h2>Something Went Wrong</h2>
              <p className="error-message">{error}</p>
              <button 
                className="retry-button"
                onClick={handleNewSearch}
              >
                Try Again
              </button>
            </div>
          )}
        </main>

        <footer className="app-footer">
          <div className="footer-content">
            <p>
              VitalMatch helps you find clinical trials that match your profile.
              Always consult with your healthcare provider before participating in any clinical trial.
            </p>
            <p className="disclaimer">
              This tool is for informational purposes only and does not constitute medical advice.
            </p>
            <p className="copyright">
              © 2024 VitalMatch. Data sourced from{' '}
              <a 
                href="https://clinicaltrials.gov" 
                target="_blank" 
                rel="noopener noreferrer"
                className="footer-link"
              >
                ClinicalTrials.gov
              </a>
            </p>
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  )
}

export default App
