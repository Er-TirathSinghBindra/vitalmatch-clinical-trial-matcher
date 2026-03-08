"""
ClinicalTrials.gov API Client
Fetches clinical trial data from ClinicalTrials.gov API v2
Requirements: TR5, 4.1, 4.5
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ClinicalTrialsAPIClient:
    """Client for fetching trials from ClinicalTrials.gov API v2"""
    
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
    DEFAULT_PAGE_SIZE = 1000  # Maximum allowed by API
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1  # seconds
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the API client
        
        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VitalMatch-Clinical-Trial-Matcher/1.0',
            'Accept': 'application/json'
        })
    
    def fetch_trials(
        self,
        query: Optional[str] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_pages: Optional[int] = None,
        updated_since: Optional[datetime] = None,
        updated_until: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch trials from ClinicalTrials.gov API with pagination
        
        Args:
            query: Search query (default: fetch all recent trials)
            page_size: Number of records per page (max 1000)
            max_pages: Maximum number of pages to fetch (None = all)
            updated_since: Only fetch trials updated since this date
            updated_until: Only fetch trials updated until this date (requires updated_since)
            
        Returns:
            List of trial dictionaries
            
        Raises:
            requests.RequestException: If API request fails after retries
        """
        all_trials = []
        page_token = None
        page_count = 0
        
        # Build query parameters
        params = self._build_query_params(query, page_size, updated_since, updated_until)
        
        logger.info(f"Starting trial fetch with query: {query}, page_size: {page_size}")
        
        while True:
            # Add page token if continuing pagination
            if page_token:
                params['pageToken'] = page_token
            
            # Fetch page with retry logic
            response_data = self._fetch_page_with_retry(params)
            
            # Extract trials from response
            studies = response_data.get('studies', [])
            all_trials.extend(studies)
            
            page_count += 1
            logger.info(f"Fetched page {page_count}: {len(studies)} trials (total: {len(all_trials)})")
            
            # Check if we should continue pagination
            next_page_token = response_data.get('nextPageToken')
            if not next_page_token:
                logger.info("No more pages available")
                break
            
            if max_pages and page_count >= max_pages:
                logger.info(f"Reached max_pages limit: {max_pages}")
                break
            
            page_token = next_page_token
            
            # Rate limiting: small delay between requests
            time.sleep(0.5)
        
        logger.info(f"Fetch complete: {len(all_trials)} total trials from {page_count} pages")
        return all_trials
    
    def _build_query_params(
        self,
        query: Optional[str],
        page_size: int,
        updated_since: Optional[datetime],
        updated_until: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Build query parameters for API request"""
        params = {
            'format': 'json',
            'pageSize': min(page_size, self.DEFAULT_PAGE_SIZE)
        }
        
        # Build query string
        if updated_since:
            # Format: YYYY-MM-DD
            start_date_str = updated_since.strftime('%Y-%m-%d')
            query_parts = []
            if query:
                query_parts.append(query)
            
            # If updated_until is provided, use date range; otherwise use open-ended range
            if updated_until:
                end_date_str = updated_until.strftime('%Y-%m-%d')
                query_parts.append(f'AREA[LastUpdatePostDate]RANGE[{start_date_str},{end_date_str}]')
            else:
                query_parts.append(f'AREA[LastUpdatePostDate]RANGE[{start_date_str},MAX]')
            
            params['query.term'] = ' AND '.join(query_parts)
        elif query:
            params['query.term'] = query
        
        return params
    
    def _fetch_page_with_retry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch a single page with exponential backoff retry logic
        
        Args:
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            requests.RequestException: If all retries fail
        """
        last_exception = None
        backoff = self.INITIAL_BACKOFF
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.debug(f"Attempt {attempt}/{self.MAX_RETRIES}: Fetching {self.BASE_URL}")
                
                response = self.session.get(
                    self.BASE_URL,
                    params=params,
                    timeout=self.timeout
                )
                
                # Raise exception for HTTP errors
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json()
                return data
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"Timeout on attempt {attempt}/{self.MAX_RETRIES}: {e}")
                
            except requests.exceptions.HTTPError as e:
                last_exception = e
                status_code = e.response.status_code
                
                # Don't retry on client errors (4xx) except 429 (rate limit)
                if 400 <= status_code < 500 and status_code != 429:
                    logger.error(f"Client error {status_code}: {e}")
                    raise
                
                logger.warning(f"HTTP error on attempt {attempt}/{self.MAX_RETRIES}: {e}")
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"Request error on attempt {attempt}/{self.MAX_RETRIES}: {e}")
            
            except ValueError as e:
                # JSON parsing error
                last_exception = e
                logger.warning(f"JSON parsing error on attempt {attempt}/{self.MAX_RETRIES}: {e}")
            
            # Exponential backoff before retry
            if attempt < self.MAX_RETRIES:
                logger.info(f"Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2  # Exponential backoff
        
        # All retries failed
        error_msg = f"Failed to fetch data after {self.MAX_RETRIES} attempts"
        logger.error(error_msg)
        raise requests.RequestException(error_msg) from last_exception
    
    def fetch_recent_trials(self, days: int = 1) -> List[Dict[str, Any]]:
        """
        Fetch trials updated in the last N days
        
        Args:
            days: Number of days to look back (default: 1)
            
        Returns:
            List of trial dictionaries
        """
        updated_since = datetime.utcnow() - timedelta(days=days)
        logger.info(f"Fetching trials updated since {updated_since.strftime('%Y-%m-%d')}")
        return self.fetch_trials(updated_since=updated_since)
    
    def fetch_trials_by_condition(
        self,
        condition: str,
        max_trials: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetch trials for a specific medical condition
        
        Args:
            condition: Medical condition to search for
            max_trials: Maximum number of trials to fetch
            
        Returns:
            List of trial dictionaries
        """
        query = f'AREA[Condition]{condition}'
        max_pages = (max_trials + self.DEFAULT_PAGE_SIZE - 1) // self.DEFAULT_PAGE_SIZE
        
        logger.info(f"Fetching trials for condition: {condition} (max: {max_trials})")
        return self.fetch_trials(query=query, max_pages=max_pages)
    
    def close(self):
        """Close the HTTP session"""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
