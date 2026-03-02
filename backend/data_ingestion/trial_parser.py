"""
Trial Data Parser and Normalizer
Parses and normalizes clinical trial data from ClinicalTrials.gov API v2
Requirements: TR5, 4.3, 4.5
"""

import logging
import re
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class TrialParser:
    """Parser for ClinicalTrials.gov API v2 response data"""
    
    # Gender mapping from API values to database values
    GENDER_MAP = {
        'MALE': 'Male',
        'FEMALE': 'Female',
        'ALL': 'All',
        'BOTH': 'All',
        'M': 'Male',
        'F': 'Female'
    }
    
    def parse_trial(self, study_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single trial from API response
        
        Args:
            study_data: Raw study data from API
            
        Returns:
            Normalized trial dictionary or None if parsing fails
        """
        try:
            protocol_section = study_data.get('protocolSection', {})
            
            # Extract NCT ID (required)
            nct_id = self._extract_nct_id(protocol_section)
            if not nct_id:
                logger.warning("Skipping trial: Missing NCT ID")
                return None
            
            # Extract title (required)
            title = self._extract_title(protocol_section)
            if not title:
                logger.warning(f"Skipping trial {nct_id}: Missing title")
                return None
            
            # Extract condition (required)
            condition = self._extract_conditions(protocol_section)
            if not condition:
                logger.warning(f"Skipping trial {nct_id}: Missing condition")
                return None
            
            # Extract optional fields
            min_age, max_age = self._extract_age_range(protocol_section)
            gender = self._extract_gender(protocol_section)
            location = self._extract_locations(protocol_section)
            inclusion_text = self._extract_inclusion_criteria(protocol_section)
            exclusion_text = self._extract_exclusion_criteria(protocol_section)
            
            trial = {
                'id': nct_id,
                'title': title,
                'condition': condition,
                'min_age': min_age,
                'max_age': max_age,
                'gender_criteria': gender,
                'location': location,
                'inclusion_text': inclusion_text,
                'exclusion_text': exclusion_text
            }
            
            logger.debug(f"Successfully parsed trial {nct_id}")
            return trial
            
        except Exception as e:
            logger.error(f"Error parsing trial: {e}", exc_info=True)
            return None
    
    def parse_trials(self, studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse multiple trials from API response
        
        Args:
            studies: List of raw study data from API
            
        Returns:
            List of normalized trial dictionaries
        """
        parsed_trials = []
        skipped_count = 0
        
        for study in studies:
            trial = self.parse_trial(study)
            if trial:
                parsed_trials.append(trial)
            else:
                skipped_count += 1
        
        logger.info(f"Parsed {len(parsed_trials)} trials, skipped {skipped_count}")
        return parsed_trials
    
    def _extract_nct_id(self, protocol_section: Dict[str, Any]) -> Optional[str]:
        """Extract NCT ID from identification module"""
        try:
            identification = protocol_section.get('identificationModule', {})
            nct_id = identification.get('nctId')
            return nct_id if nct_id else None
        except Exception as e:
            logger.debug(f"Error extracting NCT ID: {e}")
            return None
    
    def _extract_title(self, protocol_section: Dict[str, Any]) -> Optional[str]:
        """Extract title from identification module"""
        try:
            identification = protocol_section.get('identificationModule', {})
            
            # Prefer official title, fall back to brief title
            title = identification.get('officialTitle')
            if not title:
                title = identification.get('briefTitle')
            
            # Clean and truncate title
            if title:
                title = title.strip()
                # Limit to reasonable length for database
                if len(title) > 500:
                    title = title[:497] + '...'
            
            return title if title else None
        except Exception as e:
            logger.debug(f"Error extracting title: {e}")
            return None
    
    def _extract_conditions(self, protocol_section: Dict[str, Any]) -> Optional[str]:
        """Extract conditions from conditions module"""
        try:
            conditions_module = protocol_section.get('conditionsModule', {})
            conditions = conditions_module.get('conditions', [])
            
            if not conditions:
                return None
            
            # Join multiple conditions with semicolon
            condition_str = '; '.join(conditions)
            
            # Limit to reasonable length
            if len(condition_str) > 500:
                condition_str = condition_str[:497] + '...'
            
            return condition_str
        except Exception as e:
            logger.debug(f"Error extracting conditions: {e}")
            return None
    
    def _extract_age_range(self, protocol_section: Dict[str, Any]) -> tuple[Optional[int], Optional[int]]:
        """Extract min and max age from eligibility module"""
        try:
            eligibility = protocol_section.get('eligibilityModule', {})
            
            min_age = self._parse_age(eligibility.get('minimumAge'))
            max_age = self._parse_age(eligibility.get('maximumAge'))
            
            return min_age, max_age
        except Exception as e:
            logger.debug(f"Error extracting age range: {e}")
            return None, None
    
    def _parse_age(self, age_str: Optional[str]) -> Optional[int]:
        """
        Parse age string to integer years
        
        Examples:
            "18 Years" -> 18
            "65 Years" -> 65
            "6 Months" -> 0
            "N/A" -> None
        """
        if not age_str:
            return None
        
        age_str = age_str.strip().upper()
        
        # Handle N/A or similar
        if age_str in ['N/A', 'NA', 'NONE', '']:
            return None
        
        # Extract number and unit
        match = re.match(r'(\d+)\s*(YEAR|MONTH|DAY|WEEK)?S?', age_str)
        if not match:
            logger.debug(f"Could not parse age: {age_str}")
            return None
        
        number = int(match.group(1))
        unit = match.group(2) if match.group(2) else 'YEAR'
        
        # Convert to years
        if unit == 'YEAR':
            return number
        elif unit == 'MONTH':
            return number // 12  # Convert months to years (rounded down)
        elif unit == 'WEEK':
            return number // 52  # Convert weeks to years (rounded down)
        elif unit == 'DAY':
            return number // 365  # Convert days to years (rounded down)
        
        return None
    
    def _extract_gender(self, protocol_section: Dict[str, Any]) -> Optional[str]:
        """Extract gender criteria from eligibility module"""
        try:
            eligibility = protocol_section.get('eligibilityModule', {})
            sex = eligibility.get('sex', '').upper()
            
            # Map API values to database values
            return self.GENDER_MAP.get(sex, 'All')
        except Exception as e:
            logger.debug(f"Error extracting gender: {e}")
            return 'All'
    
    def _extract_locations(self, protocol_section: Dict[str, Any]) -> Optional[str]:
        """Extract location information from contacts/locations module"""
        try:
            contacts_locations = protocol_section.get('contactsLocationsModule', {})
            locations = contacts_locations.get('locations', [])
            
            if not locations:
                return None
            
            # Extract city and state from each location
            location_strings = []
            for loc in locations[:10]:  # Limit to first 10 locations
                city = loc.get('city', '')
                state = loc.get('state', '')
                country = loc.get('country', '')
                
                parts = []
                if city:
                    parts.append(city)
                if state:
                    parts.append(state)
                if country and country != 'United States':
                    parts.append(country)
                
                if parts:
                    location_strings.append(', '.join(parts))
            
            if not location_strings:
                return None
            
            # Join locations with semicolon
            location_str = '; '.join(location_strings)
            
            # Limit to reasonable length
            if len(location_str) > 1000:
                location_str = location_str[:997] + '...'
            
            return location_str
        except Exception as e:
            logger.debug(f"Error extracting locations: {e}")
            return None
    
    def _extract_inclusion_criteria(self, protocol_section: Dict[str, Any]) -> Optional[str]:
        """Extract inclusion criteria text from eligibility module"""
        try:
            eligibility = protocol_section.get('eligibilityModule', {})
            criteria_text = eligibility.get('eligibilityCriteria', '')
            
            if not criteria_text:
                return None
            
            # Try to extract inclusion section
            inclusion = self._extract_criteria_section(criteria_text, 'inclusion')
            
            # If no specific inclusion section found, use full criteria text
            if not inclusion:
                inclusion = criteria_text
            
            # Clean and limit length
            inclusion = inclusion.strip()
            if len(inclusion) > 5000:
                inclusion = inclusion[:4997] + '...'
            
            return inclusion if inclusion else None
        except Exception as e:
            logger.debug(f"Error extracting inclusion criteria: {e}")
            return None
    
    def _extract_exclusion_criteria(self, protocol_section: Dict[str, Any]) -> Optional[str]:
        """Extract exclusion criteria text from eligibility module"""
        try:
            eligibility = protocol_section.get('eligibilityModule', {})
            criteria_text = eligibility.get('eligibilityCriteria', '')
            
            if not criteria_text:
                return None
            
            # Try to extract exclusion section
            exclusion = self._extract_criteria_section(criteria_text, 'exclusion')
            
            # Clean and limit length
            if exclusion:
                exclusion = exclusion.strip()
                if len(exclusion) > 5000:
                    exclusion = exclusion[:4997] + '...'
            
            return exclusion if exclusion else None
        except Exception as e:
            logger.debug(f"Error extracting exclusion criteria: {e}")
            return None
    
    def _extract_criteria_section(self, criteria_text: str, section_type: str) -> Optional[str]:
        """
        Extract inclusion or exclusion section from criteria text
        
        Args:
            criteria_text: Full eligibility criteria text
            section_type: 'inclusion' or 'exclusion'
            
        Returns:
            Extracted section text or None
        """
        if not criteria_text:
            return None
        
        # Common patterns for section headers
        if section_type == 'inclusion':
            patterns = [
                r'Inclusion Criteria:?\s*(.*?)(?=Exclusion Criteria:?|$)',
                r'Inclusion:?\s*(.*?)(?=Exclusion:?|$)',
                r'Eligible:?\s*(.*?)(?=Ineligible:?|Exclusion:?|$)'
            ]
        else:  # exclusion
            patterns = [
                r'Exclusion Criteria:?\s*(.*?)$',
                r'Exclusion:?\s*(.*?)$',
                r'Ineligible:?\s*(.*?)$'
            ]
        
        for pattern in patterns:
            match = re.search(pattern, criteria_text, re.IGNORECASE | re.DOTALL)
            if match:
                section = match.group(1).strip()
                if section:
                    return section
        
        return None
