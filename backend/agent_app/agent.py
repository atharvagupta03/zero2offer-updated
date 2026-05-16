import os
import json
from openai import AsyncOpenAI
from backend.mcp_server.tools.profile import get_profile, save_profile, read_resume
from backend.mcp_server.tools.job_scout import search_jobs, fetch_job_description, fetch_multiple_job_descriptions

# Client will be initialized inside ask_agent to prevent crash on startup if env is missing
client = None

def get_client():
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        client = AsyncOpenAI(api_key=api_key)
    return client

AVAILABLE_TOOLS = {
    "get_profile": get_profile,
    "save_profile": save_profile,
    "read_resume": read_resume,
    "search_jobs": search_jobs,
    "fetch_job_description": fetch_job_description,
    "fetch_multiple_job_descriptions": fetch_multiple_job_descriptions
}

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_profile",
            "description": "Fetch the user's career profile (name, skills, target role) from the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_profile",
            "description": "Save or update the user's career profile JSON in the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "profile_json": {"type": "string", "description": "A JSON string of the profile data."}
                },
                "required": ["user_id", "profile_json"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_resume",
            "description": "Extract text content from a PDF or TXT resume file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_jobs",
            "description": "Search for live job postings matching a role and location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_role": {"type": "string"},
                    "location": {"type": "string", "default": "Remote"}
                },
                "required": ["target_role"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_job_description",
            "description": "Fetch the full text description of a job from its URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_multiple_job_descriptions",
            "description": "Fetch multiple job descriptions in batch from a list of URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "urls_json": {"type": "string", "description": "JSON array of URL strings."}
                },
                "required": ["urls_json"]
            }
        }
    }
]

from backend.mcp_server.tools.profile import get_profile, save_profile, read_resume, get_chat_history, add_chat_message
from backend.mcp_server.tools.job_scout import search_jobs, fetch_job_description, fetch_multiple_job_descriptions

# ... (rest of the imports and definitions stay same)

async def ask_agent(user_id: str, user_input: str) -> str:
    # 1. Fetch persistent history from DB
    history_data = get_chat_history(user_id)
    
    # 2. Build messages array with history
    messages = [
        {"role": "system", "content": f"""
            You are a Senior Career Consultant at Zero2Offer. 
            Logged-in User ID: {user_id}
            
            WORKFLOW & ANALYSIS RULES:
            1. INITIAL ANALYSIS: When analyzing a resume, you MUST follow this structure:
               - **Strengths:** Identify what the candidate is already good at.
               - **Weaknesses/Gaps:** Identify what is missing for the target role.
               - **Roadmap:** Provide a step-by-step plan to bridge those gaps.
            2. JOB SEARCH: Do NOT provide job links automatically. ONLY search for and provide job links if the user explicitly asks for them.
            3. PERSISTENCE: Use `get_profile` to recall user details. If they upload a new resume, use `read_resume` and update their profile with `save_profile`.
            4. FORMATTING: Use standard Markdown. Links must be `[Apply Here](URL)`.
            
            You have full access to the user's previous conversation history. Use it to provide contextual and personalized advice.
        """}
    ]
    
    # Add historical messages
    for msg in history_data:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current user input
    messages.append({"role": "user", "content": user_input})
    
    # Save user message to DB
    add_chat_message(user_id, "user", user_input)

    try:
        agent_client = get_client()
    except ValueError as e:
        return f"Configuration Error: {str(e)}. Please check your .env file."

    for _ in range(5):  # Max turns
        try:
            response = await agent_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TOOLS_DEFINITION,
                tool_choice="auto"
            )
        except Exception as e:
            return f"AI Error: {str(e)}"
        
        response_message = response.choices[0].message
        
        if not response_message.tool_calls:
            # Save assistant response to DB
            add_chat_message(user_id, "assistant", response_message.content)
            return response_message.content

        messages.append(response_message)
        
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            function_to_call = AVAILABLE_TOOLS[function_name]
            tool_result = function_to_call(**function_args)
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": str(tool_result),
            })
    
    return "I've processed your request as best as I could."
