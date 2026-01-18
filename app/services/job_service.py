
import requests
from typing import List, Dict, Optional

class JobSearchService:
    def __init__(self):
        self.arbeitnow_url = "https://www.arbeitnow.com/api/job-board-api"
    
    def search_jobs(self, query: str, location: str = "", limit: int = 5) -> List[Dict]:
        """
        Searches for jobs using Arbeitnow API (Free, No Auth).
        Falls back to mock data if API fails or returns no results.
        """
        jobs = []
        try:
            # Arbeitnow doesn't strongly support query params for search in the free endpoint in a standard way,
            # but we can filter results client-side or check if they added search params.
            # Official docs say it lists latest jobs. We'll try to fetch and filter.
            response = requests.get(self.arbeitnow_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                api_jobs = data.get("data", [])
                
                # Simple client-side filtering since API is limited
                for job in api_jobs:
                   title = job.get("title", "").lower()
                   description = job.get("description", "").lower()
                   q_lower = query.lower()
                   
                   if q_lower in title or q_lower in description:
                       jobs.append({
                           "title": job.get("title"),
                           "company": job.get("company_name"),
                           "location": job.get("location"),
                           "url": job.get("url"),
                           "remote": job.get("remote", False),
                           "description": job.get("description")[:200] + "..." # Truncate for display
                       })
                       
                if not jobs and not query: # Return recent jobs if no query
                     for job in api_jobs[:limit]:
                        jobs.append({
                           "title": job.get("title"),
                           "company": job.get("company_name"),
                           "location": job.get("location"),
                           "url": job.get("url"),
                           "remote": job.get("remote", False),
                           "description": job.get("description")[:200] + "..."
                       })
            
        except Exception as e:
            print(f"Error fetching jobs: {e}")

        # Fallback to Mock Data if no jobs found (reliability)
        if not jobs:
            return self._get_mock_jobs(query)
            
        return jobs[:limit]

    def _get_mock_jobs(self, query: str) -> List[Dict]:
        return [
            {
                "title": f"Senior {query.capitalize() if query else 'Software'} Engineer",
                "company": "Tech Innovators Inc.",
                "location": "Remote",
                "url": "#",
                "remote": True,
                "description": "Leading development of scalable web applications using modern technologies."
            },
             {
                "title": f"Junior {query.capitalize() if query else 'Python'} Developer",
                "company": "Startup Hub",
                "location": "New York, NY",
                "url": "#",
                "remote": False,
                "description": "Great opportunity for junior devs to learn and grow in a fast-paced environment."
            },
            {
                "title": "Product Manager",
                "company": "Global Solutions",
                "location": "London, UK",
                "url": "#",
                "remote": True,
                "description": "Overseeing product lifecycle from conception to launch."
            }
        ]

job_service = JobSearchService()
