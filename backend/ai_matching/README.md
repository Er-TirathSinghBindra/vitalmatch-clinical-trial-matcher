# AI Matching Module

This module provides AI-powered medical terminology matching for the VitalMatch Clinical Trial Matcher system.

## Components

### BedrockClient
Low-level client for Amazon Bedrock API interactions. Handles:
- Medical text analysis using Claude 3 Sonnet
- Prompt building and response parsing
- Error handling and retries
- Token limit management

### MedicalMatcher
High-level medical terminology matcher. Handles:
- Patient-to-trial matching logic
- Medical terminology variation handling
- Exclusion criteria penalty logic
- Result caching for performance

### MatchScorer
Match scoring algorithm that combines hard filters with AI soft matching. Handles:
- Scoring trials that passed hard filters
- Converting AI scores (0-1) to percentages (0-100%)
- Generating visual explanations with ✅ and ⚠️ symbols
- Ranking trials by match score (highest first)
- Returning top 3-5 matches

## Usage Examples

### Complete Workflow: Scoring and Ranking Trials

```python
from src.ai_matching import MatchScorer, PatientProfile, Trial

# Create patient profile
patient = PatientProfile(
    condition="Non-small cell lung cancer",
    age=65,
    gender="Male",
    location="New York, NY",
    distance_miles=50,
    medical_history="History of smoking, hypertension, no diabetes"
)

# Create list of trials (these would come from hard filtering)
trials = [
    Trial(
        id="NCT12345678",
        title="Phase II Study of Drug X in NSCLC Patients",
        condition="Non-small cell lung cancer",
        min_age=18,
        max_age=70,
        gender_criteria="All",
        location="Memorial Sloan Kettering, NYC",
        inclusion_text="Patients with NSCLC, history of smoking",
        exclusion_text="Active diabetes, severe heart disease"
    ),
    # ... more trials
]

# Initialize scorer (creates MedicalMatcher internally)
scorer = MatchScorer()

# Score and rank trials
results = scorer.score_and_rank_trials(
    patient_profile=patient,
    hard_filtered_trials=trials
)

# Access results (top 3-5 matches, ranked by score)
for result in results:
    print(f"Trial: {result.title}")
    print(f"Match Score: {result.match_percentage}")
    print(f"Explanation: {result.explanation}")
    print("Key Criteria:")
    for criterion in result.key_criteria:
        print(f"  {criterion}")
    print()
```

### Visual Explanations

The MatchScorer generates visual explanations with checkmarks and warnings:

```python
# Example output from key_criteria:
[
    "✅ Age requirement: 18-70 (patient: 65)",
    "✅ Location: Memorial Sloan Kettering, NYC",
    "✅ Inclusion criteria: Patient profile matches trial requirements",
    "✅ Exclusion criteria: No exclusion concerns identified",
    "✅ Excellent match: Strong alignment with trial criteria"
]

# Or with warnings:
[
    "⚠️ Age requirement: 18-60 (patient: 65)",
    "✅ Location: Boston Medical Center",
    "⚠️ Inclusion criteria: Partial match with trial requirements",
    "⚠️ Exclusion concern: Patient may meet some exclusion criteria",
    "⚠️ Moderate match: Some alignment with trial criteria"
]
```

### Match Quality Labels

```python
from src.ai_matching import MatchScorer

scorer = MatchScorer()

# Get human-readable quality labels
print(scorer.get_match_quality_label(0.95))  # "Excellent"
print(scorer.get_match_quality_label(0.80))  # "Good"
print(scorer.get_match_quality_label(0.55))  # "Moderate"
print(scorer.get_match_quality_label(0.25))  # "Poor"
```

### Basic Usage

```python
from src.ai_matching import MedicalMatcher

# Initialize matcher (creates BedrockClient internally)
matcher = MedicalMatcher(region_name="us-east-1")

# Match patient to trial
result = matcher.match_patient_to_trial(
    patient_medical_history="55-year-old male with type 2 diabetes, controlled with metformin",
    trial_inclusion_criteria="Adults aged 18-70 with type 2 diabetes mellitus",
    trial_exclusion_criteria="Severe kidney disease, active cancer"
)

# Access results
print(f"Match Score: {result['match_score']:.2f}")
print(f"Explanation: {result['explanation']}")
print(f"Inclusion Match: {result['inclusion_match']}")
print(f"Exclusion Match: {result['exclusion_match']}")
print(f"Penalty Applied: {result['exclusion_penalty_applied']}")
```

### Advanced Usage with Custom BedrockClient

```python
from src.ai_matching import BedrockClient, MedicalMatcher

# Create custom Bedrock client
bedrock_client = BedrockClient(region_name="us-west-2")

# Initialize matcher with custom client
matcher = MedicalMatcher(bedrock_client=bedrock_client)

# Use matcher
result = matcher.match_patient_to_trial(
    patient_medical_history="Patient with high blood pressure",
    trial_inclusion_criteria="Must have hypertension"
)
```

### Handling Medical Terminology Variations

The system automatically handles common medical terminology variations:

```python
# These will be recognized as equivalent:
# - "hypertension" vs "high blood pressure"
# - "diabetes" vs "diabetes mellitus" vs "high blood sugar"
# - "myocardial infarction" vs "heart attack"

result = matcher.match_patient_to_trial(
    patient_medical_history="Patient has high blood pressure",
    trial_inclusion_criteria="Must have hypertension"
)
# Will return high match score due to terminology understanding
```

### Exclusion Criteria Penalty

When exclusion criteria are violated, the match score is automatically reduced:

```python
result = matcher.match_patient_to_trial(
    patient_medical_history="Patient has diabetes and kidney disease",
    trial_inclusion_criteria="Must have diabetes",
    trial_exclusion_criteria="Cannot have kidney disease"
)

# Result will have:
# - match_score < 0.3 (penalized)
# - original_score = 0.75 (before penalty)
# - exclusion_match = True
# - exclusion_penalty_applied = True
```

### Cache Management

```python
# Check cache size
print(f"Cache entries: {matcher.get_cache_size()}")

# Clear cache (useful for testing or memory management)
matcher.clear_cache()
```

### Error Handling

```python
from src.ai_matching import MedicalMatcher, MedicalMatcherError

try:
    matcher = MedicalMatcher()
    result = matcher.match_patient_to_trial(
        patient_medical_history="",  # Invalid: empty
        trial_inclusion_criteria="Must have diabetes"
    )
except MedicalMatcherError as e:
    print(f"Matching error: {e}")
```

## Utility Functions

### normalize_medical_term

Normalize medical terminology for consistent processing:

```python
from src.ai_matching import normalize_medical_term

term = normalize_medical_term("  Hypertension  ")
# Returns: "hypertension"
```

### get_common_medical_synonyms

Get dictionary of common medical term synonyms:

```python
from src.ai_matching import get_common_medical_synonyms

synonyms = get_common_medical_synonyms()
print(synonyms['hypertension'])
# Returns: ['high blood pressure', 'elevated blood pressure', 'htn']
```

## Response Format

The `match_patient_to_trial` method returns a dictionary with:

```python
{
    'match_score': 0.85,           # Final score (0-1) after penalty
    'original_score': 0.85,        # Score before exclusion penalty
    'explanation': 'Good match...',# AI-generated explanation
    'inclusion_match': True,       # Inclusion criteria met
    'exclusion_match': False,      # Exclusion criteria violated
    'exclusion_penalty_applied': False  # Penalty was applied
}
```

## Configuration

### Exclusion Penalty Threshold

The default exclusion penalty threshold is 0.3. When exclusion criteria are violated, the score is reduced to below this threshold:

```python
# Default configuration
MedicalMatcher.EXCLUSION_PENALTY_THRESHOLD = 0.3
```

### Bedrock Model Configuration

The BedrockClient uses Claude 3 Sonnet by default:

```python
# Model configuration (in BedrockClient)
MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
MAX_RESPONSE_TOKENS = 500
TEMPERATURE = 0.3
```

## Performance Considerations

### Caching

The MedicalMatcher implements automatic caching of results:
- Cache key based on patient history, inclusion criteria, and exclusion criteria
- Reduces Bedrock API calls for repeated queries
- Use `clear_cache()` to free memory if needed

### Token Limits

Bedrock responses are limited to 500 tokens to:
- Control costs
- Ensure fast response times
- Maintain consistent explanation lengths

## Requirements Validation

This module validates the following requirements:

- **TR3**: Uses AWS managed AI services (Amazon Bedrock)
- **TR4**: Total response time for match results must be <15 seconds
- **2.4**: Handles medical terminology variations
- **2.5**: Processes inclusion and exclusion criteria text blocks
- **3.1**: System generates match scores displayed as percentages (e.g., 92%, 75%, 60%)
- **3.2**: Each trial displays in a card format with match score prominently shown
- **3.6**: Match explanations reference specific criteria that align with patient profile
- **US2**: Applies soft filters using NLP/AI for medical history matching
- **US3**: Users want to see trials ranked by match quality with clear visual explanations

## Testing

Run tests with:

```bash
# Test MatchScorer
pytest src/tests/test_match_scorer.py -v

# Test MedicalMatcher
pytest src/tests/test_medical_matcher.py -v

# Test BedrockClient
pytest src/tests/test_bedrock_client.py -v

# Test all AI matching components
pytest src/tests/test_bedrock_client.py src/tests/test_medical_matcher.py src/tests/test_match_scorer.py -v
```

## AWS Permissions Required

The Lambda function using this module needs the following IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*:*:model/anthropic.claude-3-sonnet-20240229-v1:0"
    }
  ]
}
```

## Troubleshooting

### ThrottlingException

If you encounter rate limiting:
- Implement exponential backoff in calling code
- Consider using provisioned throughput for Bedrock
- Reduce concurrent requests

### ValidationException

If you get validation errors:
- Check that patient history and criteria are non-empty strings
- Verify text length is within Bedrock limits
- Ensure proper UTF-8 encoding

### Low Match Scores

If match scores are unexpectedly low:
- Review the AI explanation for reasoning
- Check if exclusion penalty was applied
- Verify medical terminology is clear and specific
- Consider providing more detailed patient history

## Future Enhancements

Potential improvements for future versions:
- Support for multiple AI models (Claude, GPT-4, etc.)
- Batch processing for multiple trials
- Confidence intervals for match scores
- Medical ontology integration (SNOMED CT, ICD-10)
- Multi-language support
