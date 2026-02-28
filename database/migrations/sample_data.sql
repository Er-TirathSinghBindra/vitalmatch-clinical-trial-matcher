-- ============================================================================
-- VitalMatch Clinical Trial Matcher - Sample Data
-- Description: Insert sample trial data for testing and development
-- ============================================================================

\echo 'Inserting sample trial data...'

-- Sample Trial 1: Diabetes Study
INSERT INTO trials (
    id,
    title,
    condition,
    min_age,
    max_age,
    gender_criteria,
    location,
    inclusion_text,
    exclusion_text
) VALUES (
    'NCT05001234',
    'Phase III Study of Metformin in Type 2 Diabetes Patients',
    'Type 2 Diabetes',
    18,
    75,
    'All',
    'New York, NY; Boston, MA; Philadelphia, PA',
    'Adults aged 18-75 with diagnosed Type 2 Diabetes. HbA1c between 7.0-10.0%. BMI between 25-40. Willing to maintain stable diet and exercise routine.',
    'Type 1 Diabetes. Severe kidney disease (eGFR <30). History of diabetic ketoacidosis. Pregnant or breastfeeding. Severe heart failure.'
) ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    condition = EXCLUDED.condition,
    min_age = EXCLUDED.min_age,
    max_age = EXCLUDED.max_age,
    gender_criteria = EXCLUDED.gender_criteria,
    location = EXCLUDED.location,
    inclusion_text = EXCLUDED.inclusion_text,
    exclusion_text = EXCLUDED.exclusion_text,
    updated_date = CURRENT_TIMESTAMP;

-- Sample Trial 2: Lung Cancer Study
INSERT INTO trials (
    id,
    title,
    condition,
    min_age,
    max_age,
    gender_criteria,
    location,
    inclusion_text,
    exclusion_text
) VALUES (
    'NCT05002345',
    'Phase II Study of Immunotherapy in Non-Small Cell Lung Cancer',
    'Non-Small Cell Lung Cancer',
    40,
    80,
    'All',
    'Memorial Sloan Kettering Cancer Center, New York, NY; Dana-Farber Cancer Institute, Boston, MA',
    'Adults aged 40-80 with histologically confirmed NSCLC. Stage III or IV disease. ECOG performance status 0-1. History of smoking (current or former). Adequate organ function.',
    'Small cell lung cancer. Active brain metastases. Autoimmune disease requiring systemic treatment. Prior immunotherapy within 6 months. Severe COPD requiring oxygen.'
) ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    condition = EXCLUDED.condition,
    min_age = EXCLUDED.min_age,
    max_age = EXCLUDED.max_age,
    gender_criteria = EXCLUDED.gender_criteria,
    location = EXCLUDED.location,
    inclusion_text = EXCLUDED.inclusion_text,
    exclusion_text = EXCLUDED.exclusion_text,
    updated_date = CURRENT_TIMESTAMP;

-- Sample Trial 3: Hypertension Study
INSERT INTO trials (
    id,
    title,
    condition,
    min_age,
    max_age,
    gender_criteria,
    location,
    inclusion_text,
    exclusion_text
) VALUES (
    'NCT05003456',
    'Comparative Study of ACE Inhibitors vs ARBs in Hypertension',
    'Hypertension',
    30,
    70,
    'All',
    'Cleveland Clinic, Cleveland, OH; Mayo Clinic, Rochester, MN; Johns Hopkins, Baltimore, MD',
    'Adults aged 30-70 with essential hypertension. Systolic BP 140-180 mmHg. Diastolic BP 90-110 mmHg. No antihypertensive medication for at least 2 weeks.',
    'Secondary hypertension. Severe hypertension (BP >180/110). Recent myocardial infarction or stroke (within 6 months). Chronic kidney disease stage 4 or 5. Pregnancy.'
) ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    condition = EXCLUDED.condition,
    min_age = EXCLUDED.min_age,
    max_age = EXCLUDED.max_age,
    gender_criteria = EXCLUDED.gender_criteria,
    location = EXCLUDED.location,
    inclusion_text = EXCLUDED.inclusion_text,
    exclusion_text = EXCLUDED.exclusion_text,
    updated_date = CURRENT_TIMESTAMP;

-- Sample Trial 4: Breast Cancer Study (Female Only)
INSERT INTO trials (
    id,
    title,
    condition,
    min_age,
    max_age,
    gender_criteria,
    location,
    inclusion_text,
    exclusion_text
) VALUES (
    'NCT05004567',
    'Phase III Trial of Targeted Therapy in HER2-Positive Breast Cancer',
    'Breast Cancer',
    25,
    75,
    'Female',
    'MD Anderson Cancer Center, Houston, TX; Stanford Cancer Center, Palo Alto, CA',
    'Female patients aged 25-75 with HER2-positive breast cancer. Stage II or III disease. No prior chemotherapy for current diagnosis. ECOG performance status 0-2.',
    'Male breast cancer. HER2-negative disease. Metastatic disease. Severe cardiac dysfunction (LVEF <50%). Prior trastuzumab therapy.'
) ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    condition = EXCLUDED.condition,
    min_age = EXCLUDED.min_age,
    max_age = EXCLUDED.max_age,
    gender_criteria = EXCLUDED.gender_criteria,
    location = EXCLUDED.location,
    inclusion_text = EXCLUDED.inclusion_text,
    exclusion_text = EXCLUDED.exclusion_text,
    updated_date = CURRENT_TIMESTAMP;

-- Sample Trial 5: Alzheimer's Disease Study
INSERT INTO trials (
    id,
    title,
    condition,
    min_age,
    max_age,
    gender_criteria,
    location,
    inclusion_text,
    exclusion_text
) VALUES (
    'NCT05005678',
    'Early Intervention Study for Mild Cognitive Impairment and Alzheimer''s Disease',
    'Alzheimer''s Disease',
    55,
    85,
    'All',
    'University of California San Francisco, San Francisco, CA; Washington University, St. Louis, MO',
    'Adults aged 55-85 with mild cognitive impairment or early Alzheimer''s disease. MMSE score 20-26. Positive amyloid PET scan. Stable caregiver available. No significant depression.',
    'Advanced dementia (MMSE <20). Other neurological disorders (Parkinson''s, stroke). Severe psychiatric illness. Recent head trauma. Contraindications to MRI.'
) ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    condition = EXCLUDED.condition,
    min_age = EXCLUDED.min_age,
    max_age = EXCLUDED.max_age,
    gender_criteria = EXCLUDED.gender_criteria,
    location = EXCLUDED.location,
    inclusion_text = EXCLUDED.inclusion_text,
    exclusion_text = EXCLUDED.exclusion_text,
    updated_date = CURRENT_TIMESTAMP;

-- Sample Trial 6: Rheumatoid Arthritis Study
INSERT INTO trials (
    id,
    title,
    condition,
    min_age,
    max_age,
    gender_criteria,
    location,
    inclusion_text,
    exclusion_text
) VALUES (
    'NCT05006789',
    'Biologic Therapy for Moderate to Severe Rheumatoid Arthritis',
    'Rheumatoid Arthritis',
    18,
    75,
    'All',
    'Hospital for Special Surgery, New York, NY; Brigham and Women''s Hospital, Boston, MA',
    'Adults aged 18-75 with rheumatoid arthritis diagnosed by ACR criteria. Active disease with at least 6 tender and 6 swollen joints. Inadequate response to methotrexate. RF or anti-CCP positive.',
    'Other inflammatory arthritis. Active infection including tuberculosis. History of lymphoma or other malignancy within 5 years. Severe immunodeficiency. Live vaccines within 4 weeks.'
) ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    condition = EXCLUDED.condition,
    min_age = EXCLUDED.min_age,
    max_age = EXCLUDED.max_age,
    gender_criteria = EXCLUDED.gender_criteria,
    location = EXCLUDED.location,
    inclusion_text = EXCLUDED.inclusion_text,
    exclusion_text = EXCLUDED.exclusion_text,
    updated_date = CURRENT_TIMESTAMP;

-- Sample Trial 7: Asthma Study
INSERT INTO trials (
    id,
    title,
    condition,
    min_age,
    max_age,
    gender_criteria,
    location,
    inclusion_text,
    exclusion_text
) VALUES (
    'NCT05007890',
    'Novel Inhaled Therapy for Severe Asthma',
    'Asthma',
    12,
    65,
    'All',
    'National Jewish Health, Denver, CO; University of Pittsburgh Medical Center, Pittsburgh, PA',
    'Patients aged 12-65 with severe persistent asthma. FEV1 <80% predicted. At least 2 exacerbations in past year requiring oral corticosteroids. On high-dose inhaled corticosteroids and LABA.',
    'COPD or other chronic lung disease. Current smoker or >10 pack-year smoking history. Recent respiratory infection (within 4 weeks). Severe cardiovascular disease.'
) ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    condition = EXCLUDED.condition,
    min_age = EXCLUDED.min_age,
    max_age = EXCLUDED.max_age,
    gender_criteria = EXCLUDED.gender_criteria,
    location = EXCLUDED.location,
    inclusion_text = EXCLUDED.inclusion_text,
    exclusion_text = EXCLUDED.exclusion_text,
    updated_date = CURRENT_TIMESTAMP;

-- Sample Trial 8: Prostate Cancer Study (Male Only)
INSERT INTO trials (
    id,
    title,
    condition,
    min_age,
    max_age,
    gender_criteria,
    location,
    inclusion_text,
    exclusion_text
) VALUES (
    'NCT05008901',
    'Hormone Therapy Plus Radiation for Localized Prostate Cancer',
    'Prostate Cancer',
    50,
    80,
    'Male',
    'University of Texas Southwestern, Dallas, TX; UCLA Medical Center, Los Angeles, CA',
    'Male patients aged 50-80 with localized prostate cancer. Gleason score 7-9. PSA <50 ng/mL. No evidence of metastatic disease. ECOG performance status 0-1.',
    'Metastatic prostate cancer. Prior prostate cancer treatment (surgery, radiation, or hormone therapy). Severe urinary symptoms. Other active malignancy.'
) ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    condition = EXCLUDED.condition,
    min_age = EXCLUDED.min_age,
    max_age = EXCLUDED.max_age,
    gender_criteria = EXCLUDED.gender_criteria,
    location = EXCLUDED.location,
    inclusion_text = EXCLUDED.inclusion_text,
    exclusion_text = EXCLUDED.exclusion_text,
    updated_date = CURRENT_TIMESTAMP;

\echo ''
\echo 'Sample data inserted successfully!'
\echo ''

-- Display summary
SELECT 
    COUNT(*) as total_trials,
    COUNT(DISTINCT condition) as unique_conditions,
    MIN(min_age) as youngest_min_age,
    MAX(max_age) as oldest_max_age,
    COUNT(CASE WHEN gender_criteria = 'All' THEN 1 END) as all_genders,
    COUNT(CASE WHEN gender_criteria = 'Male' THEN 1 END) as male_only,
    COUNT(CASE WHEN gender_criteria = 'Female' THEN 1 END) as female_only
FROM trials;

\echo ''
\echo 'Sample trials by condition:'
SELECT condition, COUNT(*) as trial_count
FROM trials
GROUP BY condition
ORDER BY condition;

\echo ''
\echo 'Sample complete!'
