# Frontend Testing Guide

## Prerequisites

The backend API is already deployed and configured:
- **API Endpoint**: `https://2dzn9mu40e.execute-api.us-east-1.amazonaws.com/dev`
- **Database**: 5,497 clinical trials loaded
- **AI Model**: Amazon Nova Pro (working)

## Step 1: Verify Frontend Configuration

The frontend `.env` file is already configured with the correct API endpoint:

```bash
# frontend/.env
VITE_API_ENDPOINT=https://2dzn9mu40e.execute-api.us-east-1.amazonaws.com/dev
```

✅ No changes needed!

## Step 2: Install Dependencies & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will start on `http://localhost:5173` (or another port if 5173 is busy).

## Step 3: Test Cases

### Test Case 1: Breast Cancer Patient (Best Results)

This test case has been verified to work with the backend and returns 5 matches.

**Form Fields:**
- **Primary Condition**: Select "Cancer" from dropdown
- **Age**: 45
- **Gender**: Female
- **City or State**: Boston, MA
- **Search Radius**: 50 miles (default)
- **Medical History**: 
  ```
  Diagnosed with stage 2 breast cancer, HER2 positive, completed chemotherapy
  ```

**Expected Results:**
- 5 matching trials
- Top match: ~90% match score
- Processing time: ~20-25 seconds
- Trials in Boston area

---

### Test Case 2: Diabetes Patient

**Form Fields:**
- **Primary Condition**: Select "Diabetes" from dropdown
- **Age**: 55
- **Gender**: Male
- **City or State**: New York, NY
- **Search Radius**: 100 miles
- **Medical History**: 
  ```
  Type 2 diabetes diagnosed 10 years ago. Currently on metformin 1000mg twice daily. 
  HbA1c last measured at 7.8%. No complications. Hypertension controlled with lisinopril.
  ```

**Expected Results:**
- Multiple matching trials
- Trials in New York area
- Match scores based on diabetes criteria

---

### Test Case 3: Heart Disease Patient

**Form Fields:**
- **Primary Condition**: Select "Heart Disease" from dropdown
- **Age**: 62
- **Gender**: Male
- **City or State**: Los Angeles, CA
- **Search Radius**: 50 miles
- **Medical History**: 
  ```
  Coronary artery disease with stent placement 2 years ago. Currently on aspirin, 
  atorvastatin, and metoprolol. Ejection fraction 45%. No recent cardiac events.
  ```

**Expected Results:**
- Trials related to cardiovascular conditions
- Trials in Los Angeles area

---

### Test Case 4: Asthma Patient

**Form Fields:**
- **Primary Condition**: Select "Asthma" from dropdown
- **Age**: 35
- **Gender**: Female
- **City or State**: Chicago, IL
- **Search Radius**: 75 miles
- **Medical History**: 
  ```
  Moderate persistent asthma since childhood. Currently using albuterol inhaler as needed 
  and fluticasone/salmeterol twice daily. Occasional exacerbations requiring oral steroids.
  ```

**Expected Results:**
- Trials for respiratory conditions
- Trials in Chicago area

---

### Test Case 5: Custom Condition (Rheumatoid Arthritis)

**Form Fields:**
- **Primary Condition**: Select "Other (specify below)" from dropdown
- **Specify Your Condition**: Rheumatoid Arthritis
- **Age**: 48
- **Gender**: Female
- **City or State**: Boston, MA
- **Search Radius**: 50 miles
- **Medical History**: 
  ```
  Rheumatoid arthritis diagnosed 5 years ago. Currently on methotrexate 15mg weekly 
  and adalimumab biweekly. Moderate disease activity with morning stiffness lasting 
  1-2 hours. No joint damage on recent X-rays.
  ```

**Expected Results:**
- Trials matching rheumatoid arthritis
- Trials in Boston area

---

## Step 4: What to Look For

### Successful Response Should Include:

1. **Match Results Section**:
   - List of 3-5 matching trials
   - Each trial shows:
     - Trial title
     - Match score percentage (e.g., "90%")
     - Location
     - Key criteria with checkmarks (✅) and warnings (⚠️)
     - Explanation of the match

2. **Match Score Indicators**:
   - ✅ Green checkmarks for met criteria
   - ⚠️ Yellow warnings for partial matches or concerns
   - Match quality labels: "Excellent", "Good", "Moderate", "Poor"

3. **Processing Information**:
   - Total trials considered (should be 5,497)
   - Hard filtered count (varies by condition)
   - Processing time (typically 20-30 seconds)

### Error Handling to Test:

1. **Missing Required Fields**:
   - Try submitting without filling all required fields
   - Should show validation errors

2. **Invalid Age**:
   - Try entering age < 0 or > 120
   - Should show validation error

3. **Empty Medical History**:
   - Try submitting without medical history
   - Should show validation error

4. **Network Issues**:
   - The frontend has retry logic for transient failures
   - Should show appropriate error messages

---

## Step 5: Performance Expectations

- **Hard Filtering**: ~200ms (filters 5,497 trials down to 10-50)
- **AI Scoring**: ~20-25 seconds (scores 10-50 trials with Nova Pro)
- **Total Processing**: ~20-30 seconds
- **Frontend Loading**: Should show "Searching..." during processing

---

## Step 6: CloudFront Deployment (Optional)

If you want to test via CloudFront instead of localhost:

1. **Build the frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Upload to S3**:
   ```bash
   aws s3 sync dist/ s3://dev-vitalmatch-frontend-835703987264/ --delete
   ```

3. **Invalidate CloudFront cache**:
   ```bash
   aws cloudfront create-invalidation --distribution-id ET22A49XGT1L4 --paths "/*"
   ```

4. **Access via CloudFront**:
   - URL: `https://d1svuyvkh4elmx.cloudfront.net`

---

## Troubleshooting

### Issue: No matches returned
- Check that the condition exists in the database (breast cancer has most trials)
- Try increasing the search radius
- Check browser console for API errors

### Issue: API timeout
- Normal for first request (Lambda cold start)
- Retry the request
- Check CloudWatch logs for Lambda errors

### Issue: CORS errors
- API Gateway is configured with CORS headers
- Check that `.env` has correct API endpoint
- Try clearing browser cache

### Issue: Validation errors
- Ensure all required fields are filled
- Age must be 0-120
- Medical history cannot be empty
- Location must be provided

---

## Quick Test Command (API Only)

To test the API directly without the frontend:

```bash
aws lambda invoke \
  --function-name dev-vitalmatch-match-trials \
  --payload file://sample_tests/test-breast-cancer.json \
  match-trials-response.json
```

See the `sample_tests/` folder for more test payloads (diabetes, heart disease, asthma, etc.)

---

## Summary

The system is fully operational:
- ✅ Backend API deployed and working
- ✅ Database loaded with 5,497 trials
- ✅ Amazon Nova Pro AI matching working
- ✅ Frontend configured with correct API endpoint
- ✅ Test cases ready to use

Just run `npm run dev` in the frontend directory and start testing!
