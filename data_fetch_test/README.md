# Test Scripts for VitalMatch Clinical Trial Matcher

This directory contains test scripts for fetching and analyzing clinical trial data from ClinicalTrials.gov API v2.

## Scripts

### 1. `data_fetch.py`
Fetches clinical trial data from ClinicalTrials.gov API v2 and saves to CSV.

**Usage:**
```bash
python test_scripts/data_fetch.py
```

**Features:**
- Fetches trials from ClinicalTrials.gov API v2
- Extracts all fields needed for VitalMatch (NCT ID, title, condition, age, gender, location, criteria)
- Saves data to `temp_data/` subfolder with timestamp
- Uses correct API v2 syntax: `AREA[Condition]`
- No external dependencies beyond `requests`

**Default Settings:**
- Condition: Cancer
- Limit: 50 trials
- Output: `temp_data/clinical_trials_cancer_YYYYMMDD_HHMMSS.csv`

**Customize:**
Edit the last line in the script:
```python
fetch_clinical_trials(condition="Diabetes", limit=100)
```

### 2. `analyze_data.py`
Analyzes the most recent CSV file in `temp_data/` directory.

**Usage:**
```bash
python test_scripts/analyze_data.py
```

**Features:**
- Automatically finds the most recent CSV file
- Shows field completeness statistics
- Displays sample trial data
- Identifies trials with location data
- Validates data quality

**Output:**
- Total trials fetched
- Field completeness percentages
- Sample trial previews
- Location data analysis

## Directory Structure

```
test_scripts/
├── README.md              # This file
├── data_fetch.py          # Fetch trials from API
├── analyze_data.py        # Analyze fetched data
└── temp_data/             # CSV output directory
    ├── .gitignore         # Ignores CSV files in git
    └── *.csv              # Generated CSV files (not tracked)
```

## Data Fields

The scripts extract the following fields:

| Field | Description | Completeness |
|-------|-------------|--------------|
| NCT_ID | ClinicalTrials.gov identifier | 100% |
| Title | Official trial title | 100% |
| Status | Trial status (RECRUITING, COMPLETED, etc.) | 100% |
| Condition | Medical conditions studied | 100% |
| Gender | Gender criteria (Male/Female/ALL) | 100% |
| Min_Age | Minimum age requirement | ~90% |
| Max_Age | Maximum age requirement | ~34% (many have no upper limit) |
| Location | Trial locations (city, state) | ~66% |
| Eligibility_Criteria | Full inclusion/exclusion criteria text | 100% |

## Requirements

- Python 3.7+
- `requests` library

Install dependencies:
```bash
pip install requests
```

## Notes

- CSV files in `temp_data/` are ignored by git (see `.gitignore`)
- The scripts use the same data structure as VitalMatch's data ingestion pipeline
- Data is compatible with the VitalMatch trial parser
- API calls are rate-limited to respect ClinicalTrials.gov guidelines

## Examples

**Fetch Diabetes trials:**
```python
# Edit data_fetch.py, change last line to:
fetch_clinical_trials(condition="Diabetes", limit=100)
```

**Fetch Lung Cancer trials:**
```python
fetch_clinical_trials(condition="Lung Cancer", limit=200)
```

**Analyze the data:**
```bash
python test_scripts/analyze_data.py
```

## Troubleshooting

**No CSV files found:**
- Run `data_fetch.py` first to generate data

**API request failed:**
- Check internet connection
- Verify ClinicalTrials.gov API is accessible
- Try reducing the limit parameter

**Import errors:**
- Install requests: `pip install requests`

## Integration with VitalMatch

These scripts use the same API endpoints and data structure as the VitalMatch data ingestion Lambda function:
- `src/data_ingestion/clinicaltrials_api_client.py`
- `src/data_ingestion/trial_parser.py`

The CSV output can be used to:
1. Test the trial parser locally
2. Validate data quality before ingestion
3. Debug API response formats
4. Develop and test matching algorithms
