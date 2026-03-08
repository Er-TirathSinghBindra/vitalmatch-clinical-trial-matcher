# Quick Frontend Test Reference

## Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Open: `http://localhost:5173`

---

## ✅ VERIFIED TEST CASE (Use This First!)

### Breast Cancer Patient
- **Condition**: Cancer
- **Age**: 45
- **Gender**: Female
- **Location**: Boston, MA
- **Radius**: 50 miles
- **Medical History**: 
  ```
  Diagnosed with stage 2 breast cancer, HER2 positive, completed chemotherapy
  ```

**Expected**: 5 matches, top match ~90%, ~25 seconds

---

## Other Quick Tests

### Diabetes
- **Condition**: Diabetes
- **Age**: 55
- **Gender**: Male
- **Location**: New York, NY
- **Medical History**: `Type 2 diabetes, on metformin 1000mg twice daily, HbA1c 7.8%`

### Heart Disease
- **Condition**: Heart Disease
- **Age**: 62
- **Gender**: Male
- **Location**: Los Angeles, CA
- **Medical History**: `Coronary artery disease with stent, on aspirin and atorvastatin`

### Asthma
- **Condition**: Asthma
- **Age**: 35
- **Gender**: Female
- **Location**: Chicago, IL
- **Medical History**: `Moderate persistent asthma, using albuterol and fluticasone/salmeterol`

---

## What You'll See

✅ **Success**:
- 3-5 matching trials
- Match scores (0-100%)
- Checkmarks (✅) and warnings (⚠️)
- Processing time ~20-30 seconds

❌ **Errors to Test**:
- Empty fields → validation errors
- Invalid age → validation error
- No medical history → validation error

---

## System Info

- **API**: `https://2dzn9mu40e.execute-api.us-east-1.amazonaws.com/dev`
- **Database**: 5,497 trials
- **AI Model**: Amazon Nova Pro
- **CloudFront**: `https://d1svuyvkh4elmx.cloudfront.net`

---

## Deploy to CloudFront (Optional)

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://dev-vitalmatch-frontend-835703987264/ --delete
aws cloudfront create-invalidation --distribution-id ET22A49XGT1L4 --paths "/*"
```

Then access: `https://d1svuyvkh4elmx.cloudfront.net`
