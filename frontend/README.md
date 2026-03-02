# VitalMatch Frontend

React-based frontend application for the VitalMatch Clinical Trial Matcher system.

## Features

- **Patient Profile Form**: Intuitive form for entering patient information
  - Medical condition selection with common conditions
  - Age, gender, and location inputs
  - Distance radius slider
  - Medical history text area
  - Comprehensive form validation
  - WCAG 2.1 compliant and mobile-responsive

- **Processing Indicator**: Real-time progress display
  - Visual progress bar
  - Stage-by-stage updates (Searching → Filtering → AI Analysis)
  - Trial counts at each stage
  - Estimated completion time
  - Cancel search option

- **Match Results Display**: Clean presentation of trial matches
  - Summary cards showing trials searched and matches found
  - Trial match cards with scores, titles, and locations
  - Visual explanations with checkmarks (✅) and warnings (⚠️)
  - Match percentages prominently displayed
  - Responsive card layout

- **Trial Detail View**: Comprehensive trial information
  - Complete trial description and requirements
  - Highlighted eligibility criteria
  - Contact information and next steps
  - "Why this matches you" explanation
  - Save trial functionality (local storage)
  - Back navigation to results

- **Error Handling**: Robust error management
  - Global error boundary
  - User-friendly error messages
  - Retry functionality
  - Network error handling

## Technology Stack

- **React 18**: Modern React with hooks
- **Vite**: Fast build tool and dev server
- **Axios**: HTTP client for API communication
- **React Router DOM**: Client-side routing
- **CSS3**: Custom styling with responsive design

## Getting Started

### Prerequisites

- Node.js 16+ and npm

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create environment file:
   ```bash
   cp .env.example .env
   ```

3. Update `.env` with your API Gateway endpoint:
   ```
   VITE_API_ENDPOINT=https://your-api-gateway-id.execute-api.us-east-1.amazonaws.com/prod
   ```

### Development

Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Build for Production

Create a production build:
```bash
npm run build
```

The build output will be in the `dist/` directory.

Preview the production build:
```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js              # API client with axios
│   ├── components/
│   │   ├── PatientProfileForm.jsx # Patient input form
│   │   ├── PatientProfileForm.css
│   │   ├── ProcessingIndicator.jsx # Loading/progress display
│   │   ├── ProcessingIndicator.css
│   │   ├── MatchResults.jsx       # Results list display
│   │   ├── MatchResults.css
│   │   ├── TrialDetail.jsx        # Individual trial details
│   │   ├── TrialDetail.css
│   │   ├── ErrorBoundary.jsx      # Error boundary component
│   │   └── ErrorBoundary.css
│   ├── App.jsx                    # Main app component
│   ├── App.css
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Global styles
├── index.html
├── vite.config.js
├── package.json
├── .env.example
└── README.md
```

## API Integration

The frontend communicates with the backend API Gateway endpoint:

### POST /match-trials

**Request:**
```json
{
  "patient_profile": {
    "condition": "Diabetes",
    "age": 45,
    "gender": "Female",
    "location": "New York, NY",
    "distance_miles": 50,
    "medical_history": "Type 2 diabetes, hypertension..."
  }
}
```

**Response:**
```json
{
  "matches": [
    {
      "trial_id": "NCT12345678",
      "title": "Study Title",
      "match_score": 0.92,
      "explanation": "High match explanation...",
      "key_criteria": [
        "✅ Age requirement met",
        "✅ Location within range",
        "⚠️ Note about condition"
      ],
      "location": "New York, NY"
    }
  ],
  "total_trials_considered": 1247,
  "hard_filtered_count": 43,
  "processing_time_ms": 8500
}
```

## Accessibility

The application follows WCAG 2.1 Level AA guidelines:

- Semantic HTML elements
- ARIA labels and roles
- Keyboard navigation support
- Focus indicators
- Screen reader support
- Color contrast compliance
- Responsive text sizing
- Skip to main content link

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Deployment to AWS S3/CloudFront

### Automated Deployment (Recommended)

Use the deployment script for automated build and deployment:

**Linux/Mac/Git Bash:**
```bash
# From project root
./scripts/deploy-frontend.sh dev
```

**Windows PowerShell:**
```powershell
# From project root
.\scripts\deploy-frontend.ps1 -Environment dev
```

The script automatically:
- Retrieves infrastructure details from CloudFormation
- Configures environment variables
- Installs dependencies and runs tests
- Builds the production bundle
- Uploads files to S3 with optimized cache headers
- Invalidates CloudFront cache
- Displays deployment summary with URLs

### Manual Deployment

1. Build the production bundle:
   ```bash
   npm run build
   ```

2. Upload to S3 bucket:
   ```bash
   aws s3 sync dist/ s3://your-bucket-name --delete
   ```

3. Invalidate CloudFront cache:
   ```bash
   aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
   ```

### Deployment Documentation

For detailed deployment instructions, troubleshooting, and best practices, see:
- **Full Guide**: [docs/frontend-deployment.md](../docs/frontend-deployment.md)
- **Quick Reference**: [docs/deployment-quick-reference.md](../docs/deployment-quick-reference.md)

## Environment Variables

- `VITE_API_ENDPOINT`: API Gateway endpoint URL (required)

## Contributing

When adding new features:

1. Follow the existing component structure
2. Maintain accessibility standards
3. Ensure mobile responsiveness
4. Add appropriate error handling
5. Update this README if needed

## License

See LICENSE file in the project root.
