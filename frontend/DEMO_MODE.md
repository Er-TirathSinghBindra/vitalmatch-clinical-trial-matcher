# Demo Mode - Testing Without Backend

This guide shows you how to test the complete VitalMatch frontend without needing the backend API.

## Quick Start

1. **Switch to demo mode** by updating `main.jsx`:

```bash
# Open frontend/src/main.jsx and change the import
```

Change this line:
```javascript
import App from './App.jsx'
```

To this:
```javascript
import App from './App.demo.jsx'
```

2. **Install and run**:

```bash
cd frontend
npm install
npm run dev
```

3. **Open your browser** to `http://localhost:5173`

## Test Case: Complete User Journey

### Step 1: Fill Out the Form

Use this sample patient profile:

- **Primary Condition**: Cancer
- **Age**: 65
- **Gender**: Male
- **Location**: New York, NY
- **Search Radius**: 50 miles (use the slider)
- **Medical History**: 
  ```
  Non-small cell lung cancer diagnosed 6 months ago
  History of smoking (quit 5 years ago)
  High blood pressure controlled with medication
  Previous chemotherapy treatment completed 2 months ago
  ```

### Step 2: Submit and Watch Processing

- Click "Find Matching Trials"
- You'll see the processing indicator with:
  - Progress bar animating
  - Stage updates (Searching → Filtering → AI Analysis)
  - Trial counts updating in real-time
  - Elapsed time counter
  - You can test the "Cancel Search" button

### Step 3: View Results

After ~13 seconds, you'll see:
- Summary showing 1,247 trials searched, 3 matches found
- Three trial cards with different match scores (92%, 78%, 65%)
- Visual criteria indicators (✅ and ⚠️)
- Match explanations

### Step 4: View Trial Details

- Click "View Full Details" on any trial card
- You'll see:
  - Complete trial description
  - Eligibility criteria breakdown
  - "Why this matches you" explanation
  - Contact information
  - Save trial functionality (uses localStorage)

### Step 5: Test Navigation

- Click "Back to Results" to return to the list
- Click "New Search" to start over
- Test the "Save Trial" button (check localStorage in browser dev tools)

## What to Test

### Form Validation
- Try submitting without filling required fields
- Enter invalid age (negative, >120)
- Select "Other" condition and leave custom field empty
- All should show appropriate error messages

### Accessibility
- Use Tab key to navigate through form
- Use screen reader (if available)
- Check focus indicators are visible
- Verify ARIA labels are present

### Responsive Design
- Resize browser window to mobile size (375px width)
- Test on tablet size (768px width)
- Check that layout adapts properly
- Verify touch targets are large enough

### Visual Design
- Check color contrast
- Verify icons display correctly (✅, ⚠️, 📍)
- Test match score badges (different colors for 92%, 78%, 65%)
- Verify cards have proper spacing and shadows

### Local Storage
- Save a trial
- Refresh the page
- Go back to that trial detail - should show "★ Saved"
- Unsave it - should change to "☆ Save Trial"

## Mock Data Details

The demo includes 3 mock trials:

1. **92% Match** - Phase II Study (NCT12345678)
   - Perfect match with all criteria met
   - One warning about hypertension

2. **78% Match** - Immunotherapy Trial (NCT87654321)
   - Good match with most criteria
   - Needs treatment history verification

3. **65% Match** - Targeted Therapy (NCT11223344)
   - Fair match requiring genetic testing
   - Multiple warnings

## Switching Back to Production Mode

When you're ready to connect to the real API:

1. Change `main.jsx` back to:
   ```javascript
   import App from './App.jsx'
   ```

2. Configure your API endpoint in `.env`:
   ```
   VITE_API_ENDPOINT=https://your-api-gateway-url
   ```

3. Restart the dev server

## Browser Console

Open browser DevTools (F12) to see:
- Form submission data logged
- Component state changes
- Any errors or warnings

## Known Demo Limitations

- Processing always takes 13 seconds (simulated)
- Results are always the same 3 trials
- No real API calls are made
- Cancel button returns to form but doesn't stop processing
- Trial data is hardcoded (not from real ClinicalTrials.gov)

## Troubleshooting

**Issue**: Page is blank
- Check browser console for errors
- Verify you ran `npm install`
- Make sure you're using Node 16+

**Issue**: Styles look broken
- Clear browser cache
- Check that all CSS files are in `src/components/`
- Verify Vite is running without errors

**Issue**: Form won't submit
- This is expected in demo mode - check console for logged data
- Verify you changed the import in `main.jsx`

## Next Steps

After testing the demo:
1. Complete backend API implementation (tasks 4-9)
2. Deploy API Gateway
3. Switch to production mode
4. Test with real API
5. Deploy to S3/CloudFront
