import requests
import json
import csv
import os
from datetime import datetime

def fetch_clinical_trials(condition="Diabetes", limit=50):
    """
    Fetches clinical trials from ClinicalTrials.gov API v2.
    Aligned with VitalMatch data ingestion implementation.
    """
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    
    # Create temp_data directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), 'temp_data')
    os.makedirs(output_dir, exist_ok=True)
    
    # Parameters for the API v2 (correct format)
    params = {
        "query.term": f"AREA[Condition]{condition}",  # Correct API v2 syntax
        "pageSize": min(limit, 1000),  # Limit results (max is 1000 per page)
        "format": "json"  # Response format
    }
    
    print(f"Fetching {limit} trials for '{condition}'...")
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status() # Check for HTTP errors
        data = response.json()
        
        trials_list = []
        
        # The API v2 returns a 'studies' list
        if "studies" not in data:
            print("No studies found or API structure changed.")
            return

        for study in data["studies"]:
            # Navigate the nested JSON structure (Protocol Section)
            protocol = study.get("protocolSection", {})
            
            # 1. Identification Module (ID, Title)
            ident = protocol.get("identificationModule", {})
            nct_id = ident.get("nctId", "N/A")
            title = ident.get("officialTitle") or ident.get("briefTitle", "N/A")
            
            # 2. Status Module (Recruiting, Active, etc.)
            status_mod = protocol.get("statusModule", {})
            status = status_mod.get("overallStatus", "N/A")
            
            # 3. Conditions Module (Extract actual conditions from trial)
            conditions_mod = protocol.get("conditionsModule", {})
            conditions = conditions_mod.get("conditions", [])
            condition_str = "; ".join(conditions) if conditions else "N/A"
            
            # 4. Eligibility Module (The Key Data for AI)
            eligibility = protocol.get("eligibilityModule", {})
            gender = eligibility.get("sex", "ALL")
            min_age = eligibility.get("minimumAge", "N/A")
            max_age = eligibility.get("maximumAge", "N/A")
            
            # This is the "Messy Text" your AI will eventually parse
            criteria_text = eligibility.get("eligibilityCriteria", "N/A")
            
            # 5. Locations Module (Extract location data)
            contacts_locations = protocol.get("contactsLocationsModule", {})
            locations = contacts_locations.get("locations", [])
            location_list = []
            for loc in locations[:5]:  # First 5 locations
                city = loc.get("city", "")
                state = loc.get("state", "")
                if city and state:
                    location_list.append(f"{city}, {state}")
            location_str = "; ".join(location_list) if location_list else "N/A"
            
            # Append to our list
            trials_list.append({
                "NCT_ID": nct_id,
                "Title": title,
                "Status": status,
                "Condition": condition_str,
                "Gender": gender,
                "Min_Age": min_age,
                "Max_Age": max_age,
                "Location": location_str,
                "Eligibility_Criteria": criteria_text 
            })
            
        # Save to CSV (without pandas dependency)
        if trials_list:
            filename = f"clinical_trials_{condition.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = trials_list[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(trials_list)
            
            print(f"✅ Success! Saved {len(trials_list)} trials to '{filepath}'")
            print("\nFirst 2 trials:")
            for i, trial in enumerate(trials_list[:2], 1):
                print(f"\n{i}. {trial['NCT_ID']}: {trial['Title'][:80]}...")
                print(f"   Condition: {trial['Condition'][:60]}...")
                print(f"   Location: {trial['Location'][:60]}...")
        else:
            print("No trials found.")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API Request failed: {e}")

if __name__ == "__main__":
    fetch_clinical_trials(condition="Cancer", limit=50)