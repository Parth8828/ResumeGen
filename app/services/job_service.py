
import requests
from typing import List, Dict, Optional

class JobSearchService:
    def __init__(self):
        self.arbeitnow_url = "https://www.arbeitnow.com/api/job-board-api"
        self.remotive_url = "https://remotive.com/api/remote-jobs"
    
    def search_jobs(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        """
        Searches for jobs using multiple APIs (Arbeitnow + Remotive).
        Returns real jobs only - no mock data.
        """
        jobs = []
        
        # Try Arbeitnow API
        arbeitnow_jobs = self._fetch_arbeitnow_jobs(query, location)
        jobs.extend(arbeitnow_jobs)
        print(f"💼 Total jobs from Arbeitnow: {len(arbeitnow_jobs)}")
        
        # Try Remotive API (for remote jobs)
        remotive_jobs = self._fetch_remotive_jobs(query)
        jobs.extend(remotive_jobs)
        print(f"💼 Total jobs from Remotive: {len(remotive_jobs)}")
        
        # If no jobs found with query, return recent jobs instead of mock data
        if not jobs and not query:
            print("⚠️ No query provided, fetching recent jobs")
            arbeitnow_jobs = self._fetch_arbeitnow_jobs("", "")
            jobs.extend(arbeitnow_jobs[:10])
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_jobs = []
        for job in jobs:
            job_url = job.get('url', '')
            if job_url and job_url not in seen_urls:
                seen_urls.add(job_url)
                unique_jobs.append(job)
        
        print(f"✅ Returning {len(unique_jobs[:limit])} unique jobs")
        return unique_jobs[:limit]
    
    def _fetch_arbeitnow_jobs(self, query: str, location: str = "") -> List[Dict]:
        """Fetch jobs from Arbeitnow API."""
        jobs = []
        try:
            print(f"🔍 Fetching from Arbeitnow API for query: '{query}'")
            response = requests.get(self.arbeitnow_url, timeout=5)
            print(f"📡 Arbeitnow response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                api_jobs = data.get("data", [])
                print(f"📊 Arbeitnow returned {len(api_jobs)} total jobs")
                
                # Preferred locations (US, India, Remote)
                preferred_locations = ['united states', 'usa', 'us', 'india', 'remote', 'worldwide', 'anywhere']
                excluded_locations = ['germany', 'deutschland', 'berlin', 'munich', 'hamburg']
                
                # First pass: Filter by query and prioritize US/India jobs
                priority_jobs = []
                other_jobs = []
                
                # Client-side filtering
                for job in api_jobs:
                    title = job.get("title", "").lower()
                    description = job.get("description", "").lower()
                    job_location = job.get("location", "").lower()
                    tags = [tag.lower() for tag in job.get("tags", [])]
                    q_lower = query.lower() if query else ""
                    loc_lower = location.lower() if location else ""
                    
                    # Skip German jobs
                    if any(excluded in job_location for excluded in excluded_locations):
                        continue
                    
                    # More flexible matching - check title, description, and tags
                    query_match = False
                    if not q_lower:
                        query_match = True
                    else:
                        # Split query into words for better matching
                        query_words = q_lower.split()
                        # Match if ANY query word is in title, description, or tags
                        for word in query_words:
                            if (word in title or 
                                word in description or 
                                any(word in tag for tag in tags)):
                                query_match = True
                                break
                    
                    # Match location if specified
                    location_match = not loc_lower or loc_lower in job_location or "remote" in job_location
                    
                    if query_match and location_match:
                        job_data = {
                            "title": job.get("title"),
                            "company": job.get("company_name"),
                            "location": job.get("location"),
                            "url": job.get("url"),
                            "remote": job.get("remote", False),
                            "description": (job.get("description", "")[:200] + "...") if job.get("description") else "No description available.",
                            "source": "arbeitnow"
                        }
                        
                        # Prioritize US/India jobs
                        if any(pref in job_location for pref in preferred_locations):
                            priority_jobs.append(job_data)
                        else:
                            other_jobs.append(job_data)
                
                # Combine priority jobs first, then others
                jobs = priority_jobs + other_jobs
                print(f"✅ Found {len(priority_jobs)} US/India/Remote jobs, {len(other_jobs)} other jobs")
                        
                # If no matches but we have jobs from API, be more lenient
                if not jobs and api_jobs:
                    print("⚠️ Strict filtering returned 0 results, being more lenient")
                    # Just return recent jobs from the API, excluding German ones
                    for job in api_jobs[:20]:
                        job_location = job.get("location", "").lower()
                        if not any(excluded in job_location for excluded in excluded_locations):
                            jobs.append({
                                "title": job.get("title"),
                                "company": job.get("company_name"),
                                "location": job.get("location"),
                                "url": job.get("url"),
                                "remote": job.get("remote", False),
                                "description": (job.get("description", "")[:200] + "...") if job.get("description") else "No description available.",
                                "source": "arbeitnow"
                            })
                            if len(jobs) >= 10:
                                break
                
                print(f"✅ Arbeitnow filtered to {len(jobs)} matching jobs")
        except Exception as e:
            print(f"❌ Arbeitnow API error: {e}")
        
        return jobs
    
    def _fetch_remotive_jobs(self, query: str) -> List[Dict]:
        """Fetch remote jobs from Remotive API."""
        jobs = []
        try:
            response = requests.get(self.remotive_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                api_jobs = data.get("jobs", [])
                
                q_lower = query.lower() if query else ""
                
                for job in api_jobs:
                    title = job.get("title", "").lower()
                    category = job.get("category", "").lower()
                    
                    # Match query in title or category
                    if not q_lower or q_lower in title or q_lower in category:
                        jobs.append({
                            "title": job.get("title"),
                            "company": job.get("company_name"),
                            "location": "Remote",
                            "url": job.get("url"),
                            "remote": True,
                            "description": (job.get("description", "")[:200] + "...") if job.get("description") else "No description available.",
                            "source": "remotive"
                        })
                        
                        if len(jobs) >= 5:  # Limit Remotive results
                            break
        except Exception as e:
            print(f"Error fetching from Remotive: {e}")
        
        return jobs

    def _get_mock_jobs(self, query: str) -> List[Dict]:
        """
        Returns mock jobs with real job board search URLs.
        Each job links to a search on major job boards.
        """
        search_query = query if query else "Software Engineer"
        encoded_query = search_query.replace(' ', '%20')
        
        # Generate dynamic URLs for different job boards
        linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}"
        indeed_url = f"https://www.indeed.com/jobs?q={search_query.replace(' ', '+')}"
        glassdoor_url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={search_query.replace(' ', '+')}"
        
        return [
            {
                "title": f"Senior {search_query.capitalize()} Engineer",
                "company": "Tech Innovators Inc.",
                "location": "Remote",
                "url": linkedin_url,
                "remote": True,
                "description": "Leading development of scalable web applications using modern technologies. Join our team to work on cutting-edge projects with the latest tech stack.",
                "source": "mock"
            },
            {
                "title": f"Mid-Level {search_query.capitalize()} Developer",
                "company": "Startup Hub",
                "location": "New York, NY",
                "url": indeed_url,
                "remote": False,
                "description": "Great opportunity to learn and grow in a fast-paced startup environment. Work alongside experienced engineers on impactful products.",
                "source": "mock"
            },
            {
                "title": f"{search_query.capitalize()} Specialist",
                "company": "Global Solutions",
                "location": "San Francisco, CA",
                "url": glassdoor_url,
                "remote": True,
                "description": "Join a global team working on innovative solutions. Competitive salary, excellent benefits, and opportunities for career advancement.",
                "source": "mock"
            }
        ]

job_service = JobSearchService()
