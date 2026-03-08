# Sample Test Payloads

This folder contains sample test payloads for testing the Match Trials Lambda function directly.

## Usage

Test any payload using AWS CLI:

```bash
aws lambda invoke \
  --function-name dev-vitalmatch-match-trials \
  --payload file://sample_tests/test-breast-cancer.json \
  response.json
```

Then view the response:
```bash
cat response.json
```

## Available Test Cases

### 1. Breast Cancer (✅ Verified - Best Results)
**File**: `test-breast-cancer.json`

**Patient Profile**:
- Condition: Breast cancer
- Age: 45
- Gender: Female
- Location: Boston, MA
- Medical History: Stage 2 breast cancer, HER2 positive, completed chemotherapy

**Expected Results**:
- 5 matching trials
- Top match: ~90% score
- Processing time: ~25 seconds

**Test Command**:
```bash
aws lambda invoke \
  --function-name dev-vitalmatch-match-trials \
  --payload file://sample_tests/test-breast-cancer.json \
  response.json
```

---

### 2. Diabetes
**File**: `test-diabetes.json`

**Patient Profile**:
- Condition: Diabetes
- Age: 55
- Gender: Male
- Location: New York, NY
- Medical History: Type 2 diabetes, on metformin, HbA1c 7.8%

**Test Command**:
```bash
aws lambda invoke \
  --function-name dev-vitalmatch-match-trials \
  --payload file://sample_tests/test-diabetes.json \
  response.json
```

---

### 3. Heart Disease
**File**: `test-heart-disease.json`

**Patient Profile**:
- Condition: Heart disease
- Age: 62
- Gender: Male
- Location: Los Angeles, CA
- Medical History: Coronary artery disease with stent, on medications

**Test Command**:
```bash
aws lambda invoke \
  --function-name dev-vitalmatch-match-trials \
  --payload file://sample_tests/test-heart-disease.json \
  response.json
```

---

### 4. Asthma
**File**: `test-asthma.json`

**Patient Profile**:
- Condition: Asthma
- Age: 35
- Gender: Female
- Location: Chicago, IL
- Medical History: Moderate persistent asthma, on inhalers

**Test Command**:
```bash
aws lambda invoke \
  --function-name dev-vitalmatch-match-trials \
  --payload file://sample_tests/test-asthma.json \
  response.json
```

---

## Payload Format

All payloads follow this structure:

```json
{
  "body": "{\"patient_profile\":{\"condition\":\"...\",\"age\":...,\"gender\":\"...\",\"location\":\"...\",\"distance_miles\":...,\"medical_history\":\"...\"}}"
}
```

The `body` field contains a JSON-encoded string with the patient profile.

## Response Format

Successful responses will have:

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*"
  },
  "body": "{\"matches\":[...],\"total_trials_considered\":5497,\"hard_filtered_count\":25,\"processing_time_ms\":23188.85}"
}
```

The response `body` contains:
- `matches`: Array of matching trials with scores and explanations
- `total_trials_considered`: Total trials in database (5,497)
- `hard_filtered_count`: Trials after hard filtering
- `processing_time_ms`: Total processing time

## Creating Custom Test Payloads

To create your own test payload:

1. Copy an existing test file
2. Modify the patient profile fields:
   - `condition`: Medical condition
   - `age`: Patient age (0-120)
   - `gender`: Male, Female, Other, or Prefer not to say
   - `location`: City and state
   - `distance_miles`: Search radius (1-500)
   - `medical_history`: Detailed medical history

3. Ensure the JSON is properly escaped in the `body` field

## Notes

- The breast cancer test case is verified to work and returns the best results
- Processing time is typically 20-30 seconds (includes AI scoring)
- First request may be slower due to Lambda cold start
- All tests use the dev environment Lambda function
