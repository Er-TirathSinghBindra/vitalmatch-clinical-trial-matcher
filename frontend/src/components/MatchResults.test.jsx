import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MatchResults from './MatchResults'

describe('MatchResults', () => {
  const mockResults = {
    matches: [
      {
        trial_id: 'NCT12345678',
        title: 'Phase II Study of Drug X in NSCLC Patients',
        match_score: 0.92,
        explanation: 'High match: Trial specifically seeks patients with smoking history.',
        key_criteria: [
          '✅ History of smoking (required)',
          '✅ Age 18-70 (patient: 65)',
          '✅ Location: New York area',
          '⚠️ Hypertension noted - may require monitoring'
        ],
        location: 'Memorial Sloan Kettering, NYC (12 miles)'
      },
      {
        trial_id: 'NCT87654321',
        title: 'Study of Treatment Y for Advanced Cancer',
        match_score: 0.75,
        explanation: 'Good match: Most eligibility criteria met.',
        key_criteria: [
          '✅ Age requirement met',
          '✅ Location within range',
          '⚠️ Some additional screening required'
        ],
        location: 'NYU Langone Health (8 miles)'
      }
    ],
    total_trials_considered: 1247,
    hard_filtered_count: 43,
    processing_time_ms: 8500
  }

  describe('Results Display', () => {
    it('renders results header with title', () => {
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('Your Clinical Trial Matches')).toBeInTheDocument()
    })

    it('renders new search button', () => {
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByRole('button', { name: /New Search/i })).toBeInTheDocument()
    })

    it('displays summary statistics correctly', () => {
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('1,247')).toBeInTheDocument()
      expect(screen.getByText('Trials Searched')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('Best Matches Found')).toBeInTheDocument()
      expect(screen.getByText('8.5s')).toBeInTheDocument()
      expect(screen.getByText('Processing Time')).toBeInTheDocument()
    })

    it('formats processing time correctly', () => {
      const results = { ...mockResults, processing_time_ms: 12345 }
      render(<MatchResults results={results} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('12.3s')).toBeInTheDocument()
    })

    it('displays correct number of match cards', () => {
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('Top 2 Matches')).toBeInTheDocument()
      expect(screen.getByText('Phase II Study of Drug X in NSCLC Patients')).toBeInTheDocument()
      expect(screen.getByText('Study of Treatment Y for Advanced Cancer')).toBeInTheDocument()
    })
  })

  describe('Match Cards', () => {
    it('displays match score as percentage', () => {
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('92%')).toBeInTheDocument()
      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('displays trial titles', () => {
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('Phase II Study of Drug X in NSCLC Patients')).toBeInTheDocument()
      expect(screen.getByText('Study of Treatment Y for Advanced Cancer')).toBeInTheDocument()
    })

    it('displays trial locations', () => {
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('Memorial Sloan Kettering, NYC (12 miles)')).toBeInTheDocument()
      expect(screen.getByText('NYU Langone Health (8 miles)')).toBeInTheDocument()
    })

    it('displays match explanations', () => {
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('High match: Trial specifically seeks patients with smoking history.')).toBeInTheDocument()
      expect(screen.getByText('Good match: Most eligibility criteria met.')).toBeInTheDocument()
    })

    it('displays key criteria with correct icons', () => {
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('History of smoking (required)')).toBeInTheDocument()
      expect(screen.getByText('Age 18-70 (patient: 65)')).toBeInTheDocument()
      // The warning emoji adds extra characters, so use a partial match
      expect(screen.getByText(/Hypertension noted - may require monitoring/)).toBeInTheDocument()
    })

    it('displays rank numbers correctly', () => {
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('#1')).toBeInTheDocument()
      expect(screen.getByText('#2')).toBeInTheDocument()
    })

    it('applies correct CSS class based on match score', () => {
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      const cards = screen.getAllByRole('article')
      expect(cards[0]).toHaveClass('excellent') // 92% match
      expect(cards[1]).toHaveClass('good') // 75% match
    })
  })

  describe('No Results State', () => {
    it('displays no results message when matches array is empty', () => {
      const emptyResults = {
        matches: [],
        total_trials_considered: 1000,
        hard_filtered_count: 0,
        processing_time_ms: 5000
      }
      
      render(<MatchResults results={emptyResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('No Matches Found')).toBeInTheDocument()
      expect(screen.getByText(/We couldn't find any clinical trials matching your profile/i)).toBeInTheDocument()
    })

    it('shows try another search button when no results', () => {
      const emptyResults = {
        matches: [],
        total_trials_considered: 1000,
        hard_filtered_count: 0,
        processing_time_ms: 5000
      }
      
      render(<MatchResults results={emptyResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByRole('button', { name: /Try Another Search/i })).toBeInTheDocument()
    })

    it('still displays summary statistics when no matches', () => {
      const emptyResults = {
        matches: [],
        total_trials_considered: 1000,
        hard_filtered_count: 0,
        processing_time_ms: 5000
      }
      
      render(<MatchResults results={emptyResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('1,000')).toBeInTheDocument()
      expect(screen.getByText('0')).toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    it('calls onNewSearch when new search button is clicked', async () => {
      const user = userEvent.setup()
      const onNewSearch = vi.fn()
      
      render(<MatchResults results={mockResults} onViewDetails={vi.fn()} onNewSearch={onNewSearch} />)
      
      const newSearchButton = screen.getByRole('button', { name: /New Search/i })
      await user.click(newSearchButton)
      
      expect(onNewSearch).toHaveBeenCalledTimes(1)
    })

    it('calls onViewDetails with correct match data when view details button is clicked', async () => {
      const user = userEvent.setup()
      const onViewDetails = vi.fn()
      
      render(<MatchResults results={mockResults} onViewDetails={onViewDetails} onNewSearch={vi.fn()} />)
      
      const viewDetailsButtons = screen.getAllByRole('button', { name: /View Full Details/i })
      await user.click(viewDetailsButtons[0])
      
      expect(onViewDetails).toHaveBeenCalledTimes(1)
      expect(onViewDetails).toHaveBeenCalledWith(mockResults.matches[0])
    })

    it('calls onViewDetails for second match when its button is clicked', async () => {
      const user = userEvent.setup()
      const onViewDetails = vi.fn()
      
      render(<MatchResults results={mockResults} onViewDetails={onViewDetails} onNewSearch={vi.fn()} />)
      
      const viewDetailsButtons = screen.getAllByRole('button', { name: /View Full Details/i })
      await user.click(viewDetailsButtons[1])
      
      expect(onViewDetails).toHaveBeenCalledWith(mockResults.matches[1])
    })
  })

  describe('Edge Cases', () => {
    it('handles missing optional fields gracefully', () => {
      const minimalResults = {
        matches: [
          {
            trial_id: 'NCT12345678',
            title: 'Test Trial',
            match_score: 0.85
          }
        ],
        total_trials_considered: 100,
        hard_filtered_count: 10,
        processing_time_ms: 3000
      }
      
      render(<MatchResults results={minimalResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('Test Trial')).toBeInTheDocument()
      expect(screen.getByText('85%')).toBeInTheDocument()
      expect(screen.getByText('Location not specified')).toBeInTheDocument()
    })

    it('handles match with no key criteria', () => {
      const resultsWithoutCriteria = {
        matches: [
          {
            trial_id: 'NCT12345678',
            title: 'Test Trial',
            match_score: 0.80,
            key_criteria: []
          }
        ],
        total_trials_considered: 100,
        hard_filtered_count: 10,
        processing_time_ms: 3000
      }
      
      render(<MatchResults results={resultsWithoutCriteria} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('Test Trial')).toBeInTheDocument()
      expect(screen.queryByText('Key Eligibility Criteria')).not.toBeInTheDocument()
    })

    it('handles single match correctly', () => {
      const singleMatchResults = {
        matches: [mockResults.matches[0]],
        total_trials_considered: 500,
        hard_filtered_count: 20,
        processing_time_ms: 4000
      }
      
      render(<MatchResults results={singleMatchResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      expect(screen.getByText('Top 1 Matches')).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument() // Best Matches Found
    })

    it('handles results with default values when fields are missing', () => {
      const incompleteResults = {}
      
      render(<MatchResults results={incompleteResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      // Multiple "0" values exist, so check for specific context
      expect(screen.getByText('Trials Searched')).toBeInTheDocument()
      expect(screen.getByText('Best Matches Found')).toBeInTheDocument()
      expect(screen.getByText('No Matches Found')).toBeInTheDocument()
    })
  })

  describe('Match Score Classification', () => {
    it('applies "excellent" class for scores >= 85%', () => {
      const excellentResults = {
        matches: [
          { ...mockResults.matches[0], match_score: 0.92 }
        ],
        total_trials_considered: 100,
        hard_filtered_count: 10,
        processing_time_ms: 3000
      }
      
      render(<MatchResults results={excellentResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      const card = screen.getByRole('article')
      expect(card).toHaveClass('excellent')
    })

    it('applies "good" class for scores >= 70% and < 85%', () => {
      const goodResults = {
        matches: [
          { ...mockResults.matches[0], match_score: 0.75 }
        ],
        total_trials_considered: 100,
        hard_filtered_count: 10,
        processing_time_ms: 3000
      }
      
      render(<MatchResults results={goodResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      const card = screen.getByRole('article')
      expect(card).toHaveClass('good')
    })

    it('applies "fair" class for scores < 70%', () => {
      const fairResults = {
        matches: [
          { ...mockResults.matches[0], match_score: 0.65 }
        ],
        total_trials_considered: 100,
        hard_filtered_count: 10,
        processing_time_ms: 3000
      }
      
      render(<MatchResults results={fairResults} onViewDetails={vi.fn()} onNewSearch={vi.fn()} />)
      
      const card = screen.getByRole('article')
      expect(card).toHaveClass('fair')
    })
  })
})
