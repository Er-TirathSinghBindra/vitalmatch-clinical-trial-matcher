import React, { useState } from 'react'
import PatientProfileForm from './components/PatientProfileForm'
import ProcessingIndicator from './components/ProcessingIndicator'
import MatchResults from './components/MatchResults'
import TrialDetail from './components/TrialDetail'
import ErrorBoundary from './components/ErrorBoundary'
import './App.css'

// Mock data for demo mode
const MOCK_RESULTS = {
  matches: [
    {
      trial_id: 'NCT12345678',
      title: 'Phase II Study of Novel Drug X in Non-Small Cell Lung Cancer Patients',
      match_score: 0.92,
      explanation: 'High match: This trial specifically seeks patients with smoking history and your exact age range. The location is within your preferred distance.',
      key_criteria: [
        '✅ History of smoking (required)',
        '✅ Age 18-70 (you: 65)',
        '✅ Location: Memorial Sloan Kettering, NYC (12 miles)',
        '⚠️ Hypertension noted - may require additional monitoring'
      ],
      location: 'Memorial Sloan Kettering Cancer Center, New York, NY',
      description: 'This is a Phase II clinical trial evaluating the safety and efficacy of Drug X in patients with non-small cell lung cancer who have previously received chemotherapy. The study aims to determine if Drug X can improve progression-free survival compared to standard treatment.',
      inclusion_text: 'Patients must have histologically confirmed non-small cell lung cancer, be 18-70 years old, have a history of smoking, and have received at least one prior line of chemotherapy.',
      exclusion_text: 'Patients with uncontrolled hypertension (>160/100), active brain metastases, or severe cardiac disease are excluded.',
      contact_info: 'Study Coordinator: (212) 555-0123, Email: trials@mskcc.org'
    },
    {
      trial_id: 'NCT87654321',
      title: 'Immunotherapy Combination Trial for Advanced Lung Cancer',
      match_score: 0.78,
      explanation: 'Good match: Your profile aligns well with most eligibility criteria. The trial is testing a promising immunotherapy combination.',
      key_criteria: [
        '✅ Diagnosis matches trial requirements',
        '✅ Age within acceptable range',
        '✅ Location: NYU Langone Health (8 miles)',
        '⚠️ Prior treatment history needs verification'
      ],
      location: 'NYU Langone Health, New York, NY',
      description: 'A Phase III randomized trial comparing immunotherapy combination versus standard chemotherapy in patients with advanced non-small cell lung cancer.',
      inclusion_text: 'Adults 18+ with stage IV NSCLC, ECOG performance status 0-1, adequate organ function.',
      exclusion_text: 'Active autoimmune disease, prior immunotherapy, pregnancy.',
      contact_info: null
    },
    {
      trial_id: 'NCT11223344',
      title: 'Targeted Therapy Study for EGFR-Positive Lung Cancer',
      match_score: 0.65,
      explanation: 'Fair match: This trial requires specific genetic testing (EGFR mutation). Your other criteria match well.',
      key_criteria: [
        '✅ Age and location criteria met',
        '⚠️ EGFR mutation status needs confirmation',
        '⚠️ Prior targeted therapy may affect eligibility'
      ],
      location: 'Columbia University Medical Center, New York, NY',
      description: 'Evaluating a next-generation EGFR inhibitor in patients with EGFR-mutated non-small cell lung cancer who have progressed on prior EGFR therapy.',
      inclusion_text: 'Confirmed EGFR mutation (exon 19 deletion or L858R), progression on prior EGFR TKI, measurable disease.',
      exclusion_text: 'T790M mutation, symptomatic brain metastases, QTc >470ms.',
      contact_info: null
    }
  ],
  total_trials_considered: 1247,
  hard_filtered_count: 43,
  processing_time_ms: 8500
}

const APP_STATES = {
  FORM: 'form',
  PROCESSING: 'processing',
  RESULTS: 'results',
  DETAIL: 'detail'
}

function App() {
  const [appState, setAppState] = useState(APP_STATES.FORM)
  const [selectedTrial, setSelectedTrial] = useState(null)

  const handleFormSubmit = async (patientProfile) => {
    console.log('Demo Mode - Patient Profile:', patientProfile)
    
    // Show processing indicator
    setAppState(APP_STATES.PROCESSING)

    // Simulate API delay (13 seconds to match the processing indicator)
    setTimeout(() => {
      setAppState(APP_STATES.RESULTS)
    }, 13000)
  }

  const handleCancelSearch = () => {
    setAppState(APP_STATES.FORM)
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
    setSelectedTrial(null)
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
          <div className="demo-banner">
            🎭 DEMO MODE - Using mock data for testing
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

          {appState === APP_STATES.RESULTS && (
            <MatchResults 
              results={MOCK_RESULTS}
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
