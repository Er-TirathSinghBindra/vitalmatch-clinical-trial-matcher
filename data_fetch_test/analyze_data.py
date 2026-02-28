import csv
import json

# Read the CSV file
with open('clinical_trials_cancer_20260227_192353.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total trials fetched: {len(rows)}")
print(f"\nFields extracted: {list(rows[0].keys())}")

# Analyze field completeness
print("\n=== FIELD COMPLETENESS ANALYSIS ===")
for field in rows[0].keys():
    non_na_count = sum(1 for row in rows if row[field] and row[field] != 'N/A')
    percentage = (non_na_count / len(rows)) * 100
    print(f"{field:25} {non_na_count:3}/{len(rows)} ({percentage:5.1f}%)")

# Show 3 complete sample trials
print("\n=== SAMPLE TRIAL DATA ===")
for i, row in enumerate(rows[:3], 1):
    print(f"\n--- Trial {i}: {row['NCT_ID']} ---")
    print(f"Title: {row['Title'][:80]}...")
    print(f"Status: {row['Status']}")
    print(f"Condition: {row['Condition'][:60]}...")
    print(f"Gender: {row['Gender']}")
    print(f"Age Range: {row['Min_Age']} to {row['Max_Age']}")
    print(f"Location: {row['Location'][:60]}...")
    print(f"Criteria Length: {len(row['Eligibility_Criteria'])} chars")
    if row['Eligibility_Criteria'] != 'N/A':
        print(f"Criteria Preview: {row['Eligibility_Criteria'][:150]}...")

# Check for trials with locations
print("\n=== TRIALS WITH LOCATION DATA ===")
with_location = [r for r in rows if r['Location'] != 'N/A']
print(f"Trials with location: {len(with_location)}/{len(rows)}")
if with_location:
    print("\nSample trial with location:")
    sample = with_location[0]
    print(f"NCT_ID: {sample['NCT_ID']}")
    print(f"Title: {sample['Title'][:80]}...")
    print(f