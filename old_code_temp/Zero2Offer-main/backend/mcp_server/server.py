import sys
from pathlib import Path
# from dotenv import load_dotenv

# Add mcp_server directory to sys.path
CURRENT_DIR = Path(__file__).parent
sys.path.append(str(CURRENT_DIR))

# load_dotenv()

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Zero2Offer MCP Server")

# Import tools relative to mcp_server directory
from tools.profile import save_profile, get_profile, update_skills
from tools.resume import read_resume, list_resumes
from tools.readiness import evaluate_readiness
from tools.job_scout import search_jobs, fetch_job_description, fetch_multiple_job_descriptions


# Register Profile Tools
mcp.tool()(save_profile)
mcp.tool()(get_profile)
mcp.tool()(update_skills)

# Register Resume Tools
mcp.tool()(read_resume)
mcp.tool()(list_resumes)

# Register Readiness Tool
mcp.tool()(evaluate_readiness)

# Register Job_scout Tool
mcp.tool()(search_jobs)
mcp.tool()(fetch_job_description)
mcp.tool()(fetch_multiple_job_descriptions) 

if __name__ == "__main__":
    print("Zero2Offer MCP server starting...")
    mcp.run()





























