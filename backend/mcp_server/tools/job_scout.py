import os
import requests
import json
from bs4 import BeautifulSoup

def search_jobs(target_role: str, location: str = "Remote") -> str:
    api_key = os.getenv("SERPAPI_KEY")
    
    # Improved parameter handling: separation of query and location
    params = {
        "engine": "google_jobs",
        "q": target_role,
        "hl": "en",
        "api_key": api_key
    }
    
    if location.strip().lower() == "remote":
        params["q"] = f"{target_role} remote"
    else:
        params["location"] = location

    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = response.json()
        jobs = []
        for job in data.get("jobs_results", [])[:5]:
            apply_link = "Link not available"
            if job.get("apply_options"):
                apply_link = job["apply_options"][0].get("link")
            elif job.get("share_link"):
                apply_link = job.get("share_link")
                
            jobs.append({
                "title": job.get("title"),
                "company": job.get("company_name"),
                "location": job.get("location"),
                "apply_link": apply_link
            })
        
        # BeautifulSoup Fallback if API returns nothing
        if not jobs:
            return scrape_jobs_fallback(target_role, location)
            
        return json.dumps({"jobs": jobs})
    except Exception as e:
        return json.dumps({"error": str(e)})

def scrape_jobs_fallback(role: str, loc: str) -> str:
    """Uses BeautifulSoup to scrape Indeed India if API fails."""
    try:
        search_url = f"https://in.indeed.com/jobs?q={role.replace(' ', '+')}&l={loc.replace(' ', '+')}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        jobs = []
        for card in soup.select('.job_seen_beacon')[:5]:
            title_node = card.select_one('h2.jobTitle span')
            company_node = card.select_one('.companyName')
            if title_node and company_node:
                jobs.append({
                    "title": title_node.get_text(strip=True),
                    "company": company_node.get_text(strip=True),
                    "location": loc,
                    "apply_link": search_url
                })
        
        if not jobs:
            return json.dumps({"error": "No jobs found even with BeautifulSoup fallback."})
        return json.dumps({"jobs": jobs, "note": "Data fetched via BeautifulSoup fallback."})
    except Exception as e:
        return json.dumps({"error": f"Scraping failed: {str(e)}"})

def fetch_job_description(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text(separator=' ', strip=True)[:3000]
    except Exception as e:
        return f"Could not extract description: {str(e)}"

def fetch_multiple_job_descriptions(urls_json: str) -> str:
    urls = json.loads(urls_json)[:3]
    results = []
    for url in urls:
        desc = fetch_job_description(url)
        results.append(f"URL: {url}\n{desc}\n")
    return "\n\n".join(results)

def search_web(query: str) -> str:
    """Perform a web search using SerpAPI to find actual working study resources, tutorials, or articles."""
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return json.dumps({"error": "SERPAPI_KEY missing. Cannot perform live web search."})
        
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = response.json()
        results = []
        for res in data.get("organic_results", [])[:5]:
            results.append({
                "title": res.get("title"),
                "link": res.get("link"),
                "snippet": res.get("snippet")
            })
        return json.dumps({"results": results})
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})
