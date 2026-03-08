# VitalMatch Frontend Implementation

## Overview

The VitalMatch frontend is a React-based single-page application (SPA) that provides an intuitive interface for patients to find clinical trials matching their profile. The application is designed to be mobile-responsive, accessible (WCAG 2.1 compliant), and optimized for deployment on AWS S3 with CloudFront CDN.

## Architecture

### Technology Stack

- **React 18**: Modern React with functional components and hooks
- **Vite**: Fast build tool and development server
- **Axios**: HTTP client for API communication
- **React Router DOM**: Client-side routing (if needed for future expansion)
- **CSS3**: Custom styling with responsive design and accessibility features

### Component Structure

```
App (Main Container)
├── PatientProfileForm (Input)
├── ProcessingIndicator (Loading)
├── MatchResults (Results List)
│   └── TrialMatchCard (Individual Result)
├── TrialDetail (Detail View)
└── ErrorBoundary (Error Handling)
```

## Key Features

### 1. Patient Profile Form

**File**: `frontend/src/components/PatientProfileForm.jsx`

**Features**:
- Medical condition dropdown with 15 common conditions plus custom option
- Age input with validation (0-120 years)
- Gender radio buttons (Male/Female/Other/Prefer not to say)
- Location text input with helpful placeholder
- Distance radius slider (10-500 miles)
- Medical history textarea with prompts
- Comprehensive form validation
- Real-time error messages
- Disabled state during submission

**Accessibility**:
- Semantic HTML with proper labels
- ARIA attributes (aria-required, aria-invalid, aria-describedby)
- Error messages linked to inputs
- Keyboard navigation support
- Focus indicators

**Responsive Design**:
- Mobile-first approach
- Grid layout adapts to screen size
- Touch-friendly controls
- Readable text at all sizes

### 2. Processing Indicator

**File**: `frontend/src/components/ProcessingIndicator.jsx`

**Features**:
- Animated progress bar (0-100%)
- Three processing stages:
  - Searching Trials (simulated: 0-1247 trials)
  - Filtering by Criteria (simulated: 0-43 candidates)
  - AI Analysis (simulated: 0-5 matches)
- Real-time trial counts
- Elapsed time counter
- Estimated time remaining
- Cancel search button
- Visual stage indicators (checkmark, spinner, pending)

**User Experience**:
- Provides transparency during processing
- Manages user expectations with time estimates
- Allows cancellation if needed
- Smooth animations and transitions

### 3. Match Results Display

**File**: `frontend/src/components/MatchResults.jsx`

**Features**:
- Summary cards showing:
  - Total trials searched
  - Number of matches found
  - Processing time
- Trial match cards with:
  - Match percentage (0-100%)
  - Trial title and rank
  - Location information
  - Match explanation
  - Key eligibility criteria with visual indicators (✅/⚠️)
  - "View Full Details" button
- Color-coded match quality:
  - Excellent: 85%+ (green)
  - Good: 70-84% (blue)
  - Fair: <70% (orange)
- Empty state for no results
- New search button

**Visual Design**:
- Card-based layout
- Clear hierarchy
- Prominent match scores
- Easy-to-scan criteria lists
- Hover effects for interactivity

### 4. Trial Detail View

**File**: `frontend/src/components/TrialDetail.jsx`

**Features**:
- Large match score display
- Trial title and ID
- Location information
- "Why This Matches You" explanation section
- Eligibility criteria match grid
- Complete trial description
- Inclusion criteria
- Exclusion criteria
- Next steps and contact information
- Save trial functionality (localStorage)
- Back to results navigation
- Link to ClinicalTrials.gov

**Local Storage**:
- Saves trials for later reference
- Persists across sessions
- Simple JSON storage
- Visual indicator for saved trials

### 5. API Client

**File**: `frontend/src/api/client.js`

**Features**:
- Axios-based HTTP client
- Configurable base URL via environment variable
- 30-second timeout
- Request/response interceptors
- Comprehensive error handling
- Automatic retry for network errors
- User-friendly error messages
- Request logging (development)

**Error Handling**:
- Network errors
- Timeout errors
- HTTP status codes (400, 404, 429, 500, 503)
- Retry logic for transient failures
- Graceful degradation

### 6. Error Boundary

**File**: `frontend/src/components/ErrorBoundary.jsx`

**Features**:
- Catches React component errors
- Prevents app crashes
- User-friendly error display
- Development mode error details
- Reset functionality
- Error logging

## User Flow

1. **Landing**: User sees patient profile form
2. **Input**: User fills out medical information
3. **Validation**: Form validates inputs in real-time
4. **Submission**: User submits form
5. **Processing**: Processing indicator shows progress
6. **Results**: Match results display with ranked trials
7. **Detail**: User clicks to view trial details
8. **Save**: User can save trials for later
9. **Navigation**: User can return to results or start new search

## API Integration

### Endpoint: POST /match-trials

**Request Format**:
```json
{
  "patient_profile": {
    "condition": "Diabetes",
    "age": 45,
    "gender": "Female",
    "location": "New York, NY",
    "distance_miles": 50,
    "medical_history": "Type 2 diabetes diagnosed 5 years ago..."
  }
}
```

**Expected Response**:
```json
{
  "matches": [
    {
      "trial_id": "NCT12345678",
      "title": "Phase II Study of Drug X",
      "match_score": 0.92,
      "explanation": "High match explanation...",
      "key_criteria": [
        "✅ Criterion met",
        "⚠️ Note about condition"
      ],
      "location": "New York, NY",
      "description": "Trial description...",
      "inclusion_text": "Inclusion criteria...",
      "exclusion_text": "Exclusion criteria..."
    }
  ],
  "total_trials_considered": 1247,
  "hard_filtered_count": 43,
  "processing_time_ms": 8500
}
```

## Accessibility Features

### WCAG 2.1 Level AA Compliance

- **Semantic HTML**: Proper use of headings, sections, articles
- **ARIA Labels**: Descriptive labels for all interactive elements
- **Keyboard Navigation**: Full keyboard support
- **Focus Management**: Visible focus indicators
- **Color Contrast**: Meets 4.5:1 ratio for text
- **Screen Reader Support**: Proper ARIA roles and live regions
- **Form Validation**: Clear error messages linked to inputs
- **Skip Links**: Skip to main content link
- **Alt Text**: Descriptive text for icons (using aria-label)

### Responsive Design

- **Mobile-First**: Optimized for mobile devices
- **Breakpoints**:
  - Desktop: 1200px+
  - Tablet: 768px - 1199px
  - Mobile: < 768px
  - Small Mobile: < 480px
- **Touch Targets**: Minimum 44x44px for touch
- **Flexible Layouts**: Grid and flexbox
- **Readable Text**: Minimum 16px font size

### Reduced Motion Support

- Respects `prefers-reduced-motion` media query
- Disables animations for users who prefer reduced motion
- Maintains functionality without animations

## Performance Optimization

### Build Optimization

- **Code Splitting**: Automatic with Vite
- **Tree Shaking**: Removes unused code
- **Minification**: CSS and JS minified
- **Asset Optimization**: Images and fonts optimized

### Runtime Optimization

- **Lazy Loading**: Components loaded on demand
- **Memoization**: React.memo for expensive components
- **Debouncing**: Form validation debounced
- **Efficient Re-renders**: Proper use of React hooks

### Caching Strategy

- **Static Assets**: Long cache (1 year)
- **HTML**: No cache (always fresh)
- **API Responses**: No cache (real-time data)
- **CloudFront**: Edge caching for global performance

## Deployment

### AWS S3 + CloudFront

1. **Build**: `npm run build` creates optimized bundle
2. **Upload**: Sync `dist/` to S3 bucket
3. **CDN**: CloudFront serves content globally
4. **SSL**: HTTPS enforced via CloudFront
5. **WAF**: Web Application Firewall protection

### Environment Configuration

- **Development**: `npm run dev` with local API
- **Staging**: Build with staging API endpoint
- **Production**: Build with production API endpoint

### Continuous Deployment

- Automated via deployment script
- S3 sync with cache headers
- CloudFront invalidation
- Zero-downtime deployments

## Testing Strategy

### Manual Testing

- Form validation with various inputs
- API integration with real backend
- Error handling scenarios
- Mobile device testing
- Accessibility testing with screen readers
- Cross-browser testing

### Future Automated Testing

- Unit tests for components (Jest + React Testing Library)
- Integration tests for user flows
- E2E tests with Cypress
- Accessibility tests with axe-core

## Security Considerations

### Frontend Security

- **No Sensitive Data**: No PHI stored in frontend
- **HTTPS Only**: All communication encrypted
- **Input Validation**: Client-side validation (server validates too)
- **XSS Prevention**: React escapes by default
- **CORS**: Configured on backend
- **CSP**: Content Security Policy headers

### Data Privacy

- **No Tracking**: No analytics without consent
- **Local Storage**: Only non-sensitive data (saved trials)
- **Session Data**: Cleared on new search
- **No Cookies**: Stateless application

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari 14+, Chrome Mobile 90+)

## Future Enhancements

### Planned Features

- User accounts and saved searches
- Email notifications for new matching trials
- Advanced filtering options
- Trial comparison tool
- Share results functionality
- Print-friendly views
- Multi-language support

### Technical Improvements

- Progressive Web App (PWA) capabilities
- Offline support with service workers
- Real-time updates via WebSockets
- Advanced analytics
- A/B testing framework
- Performance monitoring

## Documentation

- **README.md**: Comprehensive project documentation
- **QUICKSTART.md**: 5-minute setup guide
- **DEPLOYMENT.md**: AWS deployment instructions
- **Component Comments**: Inline documentation in code

## Maintenance

### Regular Updates

- Dependency updates (monthly)
- Security patches (as needed)
- React version updates (quarterly)
- Browser compatibility checks (quarterly)

### Monitoring

- CloudFront metrics
- S3 access logs
- Error tracking (future: Sentry)
- User analytics (future: with consent)

## Conclusion

The VitalMatch frontend provides a polished, accessible, and performant user experience for clinical trial matching. Built with modern React practices and deployed on AWS infrastructure, it's designed to scale and evolve with user needs while maintaining high standards for accessibility and user experience.
