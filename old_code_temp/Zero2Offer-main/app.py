import streamlit as st
import asyncio
from pathlib import Path

from backend.agent_app.agent import ask_agent
from backend.auth import login_user, register_user

try:
    if "SERPAPI_KEY" in st.secrets:
        os.environ["SERPAPI_KEY"] = st.secrets["SERPAPI_KEY"]
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "backend" / "mcp_server" / "data" / "uploads"

st.set_page_config(page_title="Zero2Offer Assistant", page_icon="👨🏻‍💻", layout="wide")

# -- 1. Session State Initialization --
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! I'm Zero2Offer. Please use the sidebar to upload your details, and I will generate your complete Readiness Report!"}
    ]

# -- 2. Login and Signup UI --
if not st.session_state.authenticated:
    st.title("Welcome to Zero2Offer ")
    st.write("Please log in or create an account to continue.")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            log_email = st.text_input("Email")
            log_pass = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                result = login_user(log_email, log_pass)
                if result["success"]:
                    st.session_state.authenticated = True
                    st.session_state.user_id = result["user_id"]
                    st.rerun()
                else:
                    st.error(result["error"])
                    
    with tab2:
        with st.form("signup_form"):
            reg_email = st.text_input("Email")
            reg_pass = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign Up")
            
            if submitted:
                if not reg_email or not reg_pass:
                    st.error("Please fill in all fields.")
                else:
                    result = register_user(reg_email, reg_pass)
                    if result["success"]:
                        st.success("Account created successfully! You can now log in.")
                    else:
                        st.error(result["error"])
    st.stop()

# -- 3. Main App UI --
st.title(" Zero2Offer Career Assistant")

# THE NEW ONBOARDING AUTOMATOR (SIDEBAR)
with st.sidebar:
    st.header("1-Click Onboarding")
    st.write("Fill this out to generate your profile and readiness score instantly.")
    
    with st.form("onboarding_form"):
        target_role = st.text_input("Target Role (e.g., React Frontend Intern)", placeholder="Frontend Intern")
        basic_details = st.text_area("Extra Details (Skills, constraints, etc.)", placeholder="I know JS, React, Node. Looking for remote roles.")
        uploaded_file = st.file_uploader("Upload Resume (PDF/TXT)", type=["pdf", "txt"])
        
        submit_onboarding = st.form_submit_button("Analyze & Setup Profile")

    if submit_onboarding:
        if not target_role or not uploaded_file:
            st.error("Please provide at least a Target Role and a Resume.")
        else:
            # 1. Save the file
            user_folder = UPLOAD_DIR / st.session_state.user_id
            user_folder.mkdir(parents=True, exist_ok=True)
            file_path = user_folder / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success("File uploaded successfully!")

            # 2. Construct the "Master Prompt" for the One-Shot automation
            master_prompt = f"""
            I am initializing my Zero2Offer profile. Please execute the following sequence without stopping:
            
            1. Read my resume named '{uploaded_file.name}'.
            2. Combine the resume data with these extra details: "{basic_details}". 
            3. Save this combined information as my official profile using the save_profile tool.
            4. Evaluate my readiness for the role of "{target_role}" using the evaluate_readiness tool.
            
            Output a final, highly structured Readiness Report including:
            - A summary of my saved profile.
            - My Readiness Score (1-10) for the '{target_role}' role.
            - Key Strengths & Weaknesses.
            - A prioritized improvement roadmap.
            """
            
            # Display it in the chat UI
            st.session_state.messages.append({"role": "user", "content": f"*[Automated Onboarding Request for {target_role}]*"})
            
            with st.spinner("Processing your resume, saving profile, and evaluating readiness. This may take a minute..."):
                try:
                    response = asyncio.run(ask_agent(st.session_state.user_id, master_prompt))
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.divider()
    st.caption(f"User: {st.session_state.user_id}")
    if st.button("Log Out"):
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.messages = []
        st.rerun()



# -- 4. Chat Interface (For follow-up questions) --
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask follow-up questions here..."):
    # 1. Add user's message to the UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Build a "Memory Prompt" for the backend
    # We grab the last 4 messages from the session state to give the AI context
    recent_history = ""
    for m in st.session_state.messages[-5:-1]: # Exclude the prompt we just appended
        role_name = "AI ASSISTANT" if m['role'] == "assistant" else "USER"
        recent_history += f"{role_name} SAID:\n{m['content']}\n\n"

    # Wrap the user's prompt with the memory context
    context_aware_prompt = f"""
    Here is the recent conversation history for context:
    {recent_history}
    
    Now, please fulfill this new user request based on the context above:
    USER REQUEST: {prompt}
    """

    with st.chat_message("assistant"):
        with st.spinner("Getting responces... (This may take a minute)"):
            try:
                # Send the memory-injected prompt to the agent!
                response = asyncio.run(ask_agent(st.session_state.user_id, context_aware_prompt))
                st.markdown(response)
                # Save the AI's clean response to the UI history
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {str(e)}")







































