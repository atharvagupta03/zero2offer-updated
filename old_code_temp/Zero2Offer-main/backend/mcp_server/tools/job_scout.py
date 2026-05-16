import os
import requests
import json
from bs4 import BeautifulSoup

def search_jobs(target_role: str, location: str = "Remote") -> str:
    """
    Searches for real-world job postings matching the target role and location.
    Returns a JSON string of job listings with their direct apply links.
    """
    api_key = os.getenv("SERPAPI_KEY")
    
    if not api_key:
        mock_jobs = [
            {
                "title": f"{target_role} - Early Career", 
                "company": "XYZ Company 2", 
                "location": location, 
                "apply_link": "https://example.com/apply/technova"
            },
            {
                "title": f"Junior {target_role}", 
                "company": "XYZ Company 2", 
                "location": "Remote", 
                "apply_link": "https://example.com/apply/datasphere"
            },
            {
                "title": f"{target_role} (New Grad)", 
                "company": "XYZ Company 3", 
                "location": location, 
                "apply_link": "https://example.com/apply/cloudfront"
            }
        ]
        return json.dumps({"jobs": mock_jobs, "note": "Showing mock data. Add SERPAPI_KEY to .env for real Google Jobs results."})

    # Base parameters
    params = {
        "engine": "google_jobs",
        "q": target_role,
        "hl": "en",
        "api_key": api_key
    }
    
    # Google Jobs crashes if we use 'Remote' as the location, to remove that issue.
    if location.strip().lower() == "remote":
        params["q"] = f"{target_role} remote"  
    else:
        params["location"] = location          
    
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        data = response.json()
        
        jobs = []
        for job in data.get("jobs_results", [])[:5]: # Get the top 5 matches
            # hunt for the application link
            apply_link = "Link not available"
            
            # 1. First choice: The direct 'Apply' buttons Google provides
            if job.get("apply_options"):
                apply_link = job["apply_options"][0].get("link")
            # 2. Second choice: The share link (takes you to the Google Jobs page)
            elif job.get("share_link"):
                apply_link = job.get("share_link")
            # 3. Third choice: Related links
            elif job.get("related_links"):
                apply_link = job["related_links"][0].get("link")
                
            jobs.append({
                "title": job.get("title", "Unknown Title"),
                "company": job.get("company_name", "Unknown Company"),
                "location": job.get("location", "Location not specified"),
                "apply_link": apply_link,
            })
        return json.dumps({"jobs": jobs})
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch jobs: {str(e)}"})


def fetch_job_description(url: str) -> str:
    """
    Fetches and extracts the text from a job application URL.
    """
    if "example.com" in url or "Link not available" in url:
        return "MOCK JOB DESCRIPTION: We are seeking a highly motivated candidate to join our team. The ideal candidate has strong technical skills and a solid understanding of our core tech stack. You will be helping us build and optimize great products."

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        # Return the first 3000 characters to keep the LLM context window manageable
        return text[:3000]
    except Exception as e:
        return f"Could not extract description: {str(e)}"


def fetch_multiple_job_descriptions(urls_json: str) -> str:
    """
    Takes a JSON string list of job URLs and fetches the descriptions for the jobs searched.
    This prevents the AI from getting stuck in tool loops while batching.
    """
    try:
        urls = json.loads(urls_json)
        if not isinstance(urls, list):
            return "Error: urls_json must be a JSON list of strings."
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for URLs."

    # Limit to top 3 to cut the cost of API call and to reduce the context window limit as well,
    top_urls = urls[:3]
    combined_descriptions = []

    for i, url in enumerate(top_urls):
        desc = fetch_job_description(url)
        combined_descriptions.append(f"--- JOB {i+1} URL: {url} ---\n{desc}\n")
    
    return "\n\n".join(combined_descriptions)












































