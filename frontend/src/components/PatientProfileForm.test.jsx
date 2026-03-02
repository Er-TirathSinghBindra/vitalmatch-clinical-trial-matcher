import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PatientProfileForm from './PatientProfileForm'

describe('PatientProfileForm', () => {
  describe('Form Rendering', () => {
    it('renders all form sections', () => {
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      expect(screen.getByText('Find Your Clinical Trial Match')).toBeInTheDocument()
      expect(screen.getByText('Medical Condition')).toBeInTheDocument()
      expect(screen.getByText('Demographics')).toBeInTheDocument()
      expect(screen.getByText('Location')).toBeInTheDocument()
      // Use getAllByText since "Medical History" appears as both heading and label
      expect(screen.getAllByText(/Medical History/)[0]).toBeInTheDocument()
    })

    it('renders all required form fields', () => {
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      expect(screen.getByLabelText(/Primary Condition/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Age/i)).toBeInTheDocument()
      expect(screen.getByRole('radiogroup')).toBeInTheDocument()
      expect(screen.getByLabelText(/City or State/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Medical History/i)).toBeInTheDocument()
    })

    it('renders submit button with correct text', () => {
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      expect(screen.getByRole('button', { name: /Find Matching Trials/i })).toBeInTheDocument()
    })

    it('shows loading state when isLoading is true', () => {
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={true} />)
      
      const submitButton = screen.getByRole('button')
      expect(submitButton).toHaveTextContent('Searching...')
      expect(submitButton).toBeDisabled()
    })
  })

  describe('Form Validation - Required Fields', () => {
    it('shows error when condition is not selected', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Please select a medical condition')).toBeInTheDocument()
    })

    it('shows error when age is not provided', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Please enter your age')).toBeInTheDocument()
    })

    it('shows error when gender is not selected', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Please select your gender')).toBeInTheDocument()
    })

    it('shows error when location is not provided', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Please enter your location')).toBeInTheDocument()
    })

    it('shows error when medical history is not provided', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Please provide your medical history')).toBeInTheDocument()
    })
  })

  describe('Form Validation - Age Range', () => {
    it('shows error when age is less than 0', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const ageInput = screen.getByLabelText(/Age/i)
      await user.type(ageInput, '-5')
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Please enter a valid age between 0 and 120')).toBeInTheDocument()
    })

    it('shows error when age is greater than 120', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const ageInput = screen.getByLabelText(/Age/i)
      await user.type(ageInput, '150')
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Please enter a valid age between 0 and 120')).toBeInTheDocument()
    })

    it('accepts valid age at boundary (0)', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<PatientProfileForm onSubmit={onSubmit} isLoading={false} />)
      
      // Fill all required fields
      await user.selectOptions(screen.getByLabelText(/Primary Condition/i), 'Diabetes')
      await user.type(screen.getByLabelText(/Age/i), '0')
      await user.click(screen.getByLabelText('Male'))
      await user.type(screen.getByLabelText(/City or State/i), 'New York')
      await user.type(screen.getByLabelText(/Medical History/i), 'No significant medical history')
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ age: 0 })
      )
    })

    it('accepts valid age at boundary (120)', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<PatientProfileForm onSubmit={onSubmit} isLoading={false} />)
      
      // Fill all required fields
      await user.selectOptions(screen.getByLabelText(/Primary Condition/i), 'Diabetes')
      await user.type(screen.getByLabelText(/Age/i), '120')
      await user.click(screen.getByLabelText('Male'))
      await user.type(screen.getByLabelText(/City or State/i), 'New York')
      await user.type(screen.getByLabelText(/Medical History/i), 'No significant medical history')
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ age: 120 })
      )
    })

    it('accepts valid age in middle range', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<PatientProfileForm onSubmit={onSubmit} isLoading={false} />)
      
      // Fill all required fields
      await user.selectOptions(screen.getByLabelText(/Primary Condition/i), 'Diabetes')
      await user.type(screen.getByLabelText(/Age/i), '65')
      await user.click(screen.getByLabelText('Male'))
      await user.type(screen.getByLabelText(/City or State/i), 'New York')
      await user.type(screen.getByLabelText(/Medical History/i), 'No significant medical history')
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ age: 65 })
      )
    })
  })

  describe('Form Validation - Custom Condition', () => {
    it('shows custom condition field when "Other" is selected', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const conditionSelect = screen.getByLabelText(/Primary Condition/i)
      await user.selectOptions(conditionSelect, 'Other (specify below)')
      
      expect(screen.getByLabelText(/Specify Your Condition/i)).toBeInTheDocument()
    })

    it('shows error when "Other" is selected but custom condition is not provided', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const conditionSelect = screen.getByLabelText(/Primary Condition/i)
      await user.selectOptions(conditionSelect, 'Other (specify below)')
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Please specify your condition')).toBeInTheDocument()
    })

    it('accepts custom condition when provided', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<PatientProfileForm onSubmit={onSubmit} isLoading={false} />)
      
      // Fill all required fields with custom condition
      await user.selectOptions(screen.getByLabelText(/Primary Condition/i), 'Other (specify below)')
      await user.type(screen.getByLabelText(/Specify Your Condition/i), 'Rheumatoid Arthritis')
      await user.type(screen.getByLabelText(/Age/i), '55')
      await user.click(screen.getByLabelText('Female'))
      await user.type(screen.getByLabelText(/City or State/i), 'Boston')
      await user.type(screen.getByLabelText(/Medical History/i), 'Diagnosed with RA 5 years ago')
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ condition: 'Rheumatoid Arthritis' })
      )
    })
  })

  describe('Form Interaction', () => {
    it('clears error when user starts typing in a field', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      // Trigger validation error
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Please enter your age')).toBeInTheDocument()
      
      // Start typing in age field
      const ageInput = screen.getByLabelText(/Age/i)
      await user.type(ageInput, '30')
      
      // Error should be cleared
      expect(screen.queryByText('Please enter your age')).not.toBeInTheDocument()
    })

    it('updates distance slider value', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const slider = screen.getByLabelText(/Search radius:/i)
      expect(slider).toHaveValue('50')
      
      fireEvent.change(slider, { target: { value: '100' } })
      
      expect(slider).toHaveValue('100')
      expect(screen.getByText('Search Radius: 100 miles')).toBeInTheDocument()
    })

    it('allows selecting different gender options', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const maleRadio = screen.getByLabelText('Male')
      const femaleRadio = screen.getByLabelText('Female')
      const otherRadio = screen.getByLabelText('Other')
      
      await user.click(maleRadio)
      expect(maleRadio).toBeChecked()
      
      await user.click(femaleRadio)
      expect(femaleRadio).toBeChecked()
      expect(maleRadio).not.toBeChecked()
      
      await user.click(otherRadio)
      expect(otherRadio).toBeChecked()
      expect(femaleRadio).not.toBeChecked()
    })
  })

  describe('Form Submission', () => {
    it('calls onSubmit with correct data when form is valid', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<PatientProfileForm onSubmit={onSubmit} isLoading={false} />)
      
      // Fill all required fields
      await user.selectOptions(screen.getByLabelText(/Primary Condition/i), 'Diabetes')
      await user.type(screen.getByLabelText(/Age/i), '65')
      await user.click(screen.getByLabelText('Male'))
      await user.type(screen.getByLabelText(/City or State/i), 'New York, NY')
      
      const slider = screen.getByLabelText(/Search radius:/i)
      fireEvent.change(slider, { target: { value: '75' } })
      
      await user.type(screen.getByLabelText(/Medical History/i), 'Type 2 diabetes, hypertension')
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(onSubmit).toHaveBeenCalledTimes(1)
      expect(onSubmit).toHaveBeenCalledWith({
        condition: 'Diabetes',
        age: 65,
        gender: 'Male',
        location: 'New York, NY',
        distance_miles: 75, // Component should convert to number
        medical_history: 'Type 2 diabetes, hypertension'
      })
    })

    it('does not call onSubmit when form is invalid', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<PatientProfileForm onSubmit={onSubmit} isLoading={false} />)
      
      // Only fill some fields
      await user.selectOptions(screen.getByLabelText(/Primary Condition/i), 'Diabetes')
      await user.type(screen.getByLabelText(/Age/i), '65')
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('disables all inputs when isLoading is true', () => {
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={true} />)
      
      expect(screen.getByLabelText(/Primary Condition/i)).toBeDisabled()
      expect(screen.getByLabelText(/Age/i)).toBeDisabled()
      expect(screen.getByLabelText('Male')).toBeDisabled()
      expect(screen.getByLabelText(/City or State/i)).toBeDisabled()
      expect(screen.getByLabelText(/Search radius:/i)).toBeDisabled()
      expect(screen.getByLabelText(/Medical History/i)).toBeDisabled()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels for required fields', () => {
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      expect(screen.getByLabelText(/Primary Condition/i)).toHaveAttribute('aria-required', 'true')
      expect(screen.getByLabelText(/Age/i)).toHaveAttribute('aria-required', 'true')
      expect(screen.getByLabelText(/City or State/i)).toHaveAttribute('aria-required', 'true')
      expect(screen.getByLabelText(/Medical History/i)).toHaveAttribute('aria-required', 'true')
    })

    it('sets aria-invalid when field has error', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      expect(screen.getByLabelText(/Primary Condition/i)).toHaveAttribute('aria-invalid', 'true')
      expect(screen.getByLabelText(/Age/i)).toHaveAttribute('aria-invalid', 'true')
    })

    it('associates error messages with form fields', async () => {
      const user = userEvent.setup()
      render(<PatientProfileForm onSubmit={vi.fn()} isLoading={false} />)
      
      const submitButton = screen.getByRole('button', { name: /Find Matching Trials/i })
      await user.click(submitButton)
      
      const ageInput = screen.getByLabelText(/Age/i)
      expect(ageInput).toHaveAttribute('aria-describedby', 'age-error')
    })
  })
})
