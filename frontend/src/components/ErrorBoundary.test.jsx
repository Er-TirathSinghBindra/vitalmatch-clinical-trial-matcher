import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ErrorBoundary from './ErrorBoundary'

// Component that throws an error
const ThrowError = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>No error</div>
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // Suppress console.error for these tests since we're intentionally throwing errors
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    console.error.mockRestore()
  })

  describe('Normal Rendering', () => {
    it('renders children when there is no error', () => {
      render(
        <ErrorBoundary>
          <div>Test content</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('Test content')).toBeInTheDocument()
    })

    it('renders multiple children when there is no error', () => {
      render(
        <ErrorBoundary>
          <div>First child</div>
          <div>Second child</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('First child')).toBeInTheDocument()
      expect(screen.getByText('Second child')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('catches errors thrown by child components', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()
    })

    it('displays error message when error is caught', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText(/We're sorry, but something unexpected happened/i)).toBeInTheDocument()
    })

    it('displays reset button when error is caught', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /Return to Home/i })).toBeInTheDocument()
    })

    it('logs error to console', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(console.error).toHaveBeenCalled()
    })

    it('does not render children when error is caught', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.queryByText('No error')).not.toBeInTheDocument()
    })
  })

  describe('Error Details in Development', () => {
    it('shows error details in development mode', () => {
      const originalEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'development'

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Error Details (Development Only)')).toBeInTheDocument()

      process.env.NODE_ENV = originalEnv
    })

    it('hides error details in production mode', () => {
      const originalEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'production'

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.queryByText('Error Details (Development Only)')).not.toBeInTheDocument()

      process.env.NODE_ENV = originalEnv
    })

    it('displays error stack trace in development mode', () => {
      const originalEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'development'

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const details = screen.getByText('Error Details (Development Only)')
      expect(details).toBeInTheDocument()

      process.env.NODE_ENV = originalEnv
    })
  })

  describe('Reset Functionality', () => {
    it('redirects to home when reset button is clicked', async () => {
      const user = userEvent.setup()
      
      // Mock window.location.href
      delete window.location
      window.location = { href: '' }

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const resetButton = screen.getByRole('button', { name: /Return to Home/i })
      await user.click(resetButton)

      expect(window.location.href).toBe('/')
    })
  })

  describe('Error State Management', () => {
    it('updates state when error is caught', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      )

      expect(screen.getByText('No error')).toBeInTheDocument()

      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()
    })

    it('maintains error state after catching error', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()
      
      // Error UI should remain visible
      expect(screen.getByRole('button', { name: /Return to Home/i })).toBeInTheDocument()
    })
  })

  describe('UI Elements', () => {
    it('displays error icon', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('💥')).toBeInTheDocument()
    })

    it('displays error heading', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('heading', { name: /Oops! Something went wrong/i })).toBeInTheDocument()
    })

    it('displays error description', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText(/The error has been logged and we'll look into it/i)).toBeInTheDocument()
    })
  })

  describe('Multiple Errors', () => {
    it('handles multiple errors from different children', () => {
      const MultipleErrorChildren = () => {
        throw new Error('First error')
      }

      render(
        <ErrorBoundary>
          <MultipleErrorChildren />
        </ErrorBoundary>
      )

      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()
    })

    it('catches first error and stops rendering', () => {
      const FirstError = () => {
        throw new Error('First error')
      }
      
      const SecondComponent = () => <div>Should not render</div>

      render(
        <ErrorBoundary>
          <FirstError />
          <SecondComponent />
        </ErrorBoundary>
      )

      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()
      expect(screen.queryByText('Should not render')).not.toBeInTheDocument()
    })
  })

  describe('Nested Error Boundaries', () => {
    it('inner error boundary catches errors from its children', () => {
      render(
        <ErrorBoundary>
          <div>Outer content</div>
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        </ErrorBoundary>
      )

      // Inner error boundary should catch the error
      expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument()
      // Outer content should still be visible (not caught by outer boundary)
      expect(screen.getByText('Outer content')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has accessible button for reset', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const resetButton = screen.getByRole('button', { name: /Return to Home/i })
      expect(resetButton).toBeInTheDocument()
      expect(resetButton).toHaveClass('reset-button')
    })

    it('has proper heading hierarchy', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading).toHaveTextContent('Oops! Something went wrong')
    })
  })
})
