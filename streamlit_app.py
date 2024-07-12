import streamlit as st
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, FileReadTool, FileWriteTool
import chromadb  # For vector database
import toml  # For secret management
import os
import hashlib  # For password hashing

# --- Authentication ---

# Function to hash passwords (replace with a more secure method if needed)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Load credentials from secrets.toml
try:
    secrets = toml.load("secrets.toml")
    username = secrets["credentials"]["username"]
    hashed_password = secrets["credentials"]["password"]
except FileNotFoundError:
    st.error(
        "secrets.toml file not found. Please create one with username and password."
    )
    st.stop()


# Login form
def login():
    """Shows a login form and authenticates the user."""

    st.sidebar.header("Login")
    entered_username = st.sidebar.text_input("Username")
    entered_password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if (
            entered_username == username
            and hash_password(entered_password) == hashed_password
        ):
            st.sidebar.success("Logged in!")
            st.session_state.logged_in = True  # Set session state
        else:
            st.sidebar.error("Invalid username or password.")


# Check if already logged in
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# Show login form if not logged in
if not st.session_state.logged_in:
    login()
    st.stop()  # Stop execution until logged in


# --- API Key Management ---


# Function to store API keys securely (replace with more robust methods like encrypted storage if needed)
def store_api_key(api_key, api_name):
    secrets = toml.load("secrets.toml")
    secrets["api_keys"][api_name] = api_key
    with open("secrets.toml", "w") as f:
        toml.dump(secrets, f)


# API key form
def api_key_form():
    """Shows a form for adding API keys."""

    st.sidebar.header("API Keys")
    api_name = st.sidebar.selectbox("API Name", ["serper", "openai", "other"])
    api_key = st.sidebar.text_input(f"{api_name.title()} API Key", type="password")

    if st.sidebar.button("Add API Key"):
        store_api_key(api_key, api_name)
        st.sidebar.success(f"{api_name.title()} API key added!")


# Load existing API keys
try:
    secrets = toml.load("secrets.toml")
    api_keys = secrets.get("api_keys", {})
except FileNotFoundError:
    api_keys = {}


# Display API key form
api_key_form()


# --- crewAI Examples ---


# Define a dictionary of available crewAI examples
crewai_examples = {
    "Prepare for meetings": {
        "description": "Prepare for your next meeting by summarizing documents and generating key talking points.",
        "agents": ["Researcher", "Analyst", "Writer"],
        "tasks": ["Summarize Document", "Analyze Trends", "Generate Talking Points"],
    },
    "Trip Planner Crew": {
        "description": "Plan your next trip with the help of AI agents who can find flights, hotels, and activities.",
        "agents": ["Travel Agent", "Researcher", "Budget Analyst"],
        "tasks": [
            "Find Flights",
            "Find Hotels",
            "Find Activities",
            "Calculate Budget",
        ],
    },
    "Create Instagram Post": {
        "description": "Generate an engaging Instagram post with relevant hashtags and captions.",
        "agents": ["Content Creator", "Image Editor", "Hashtag Generator"],
        "tasks": ["Write Caption", "Edit Image", "Generate Hashtags"],
    },
    "Marketing Campaign": {
        "description": "Generate a marketing plan, target audience research, and ad copy.",
        "agents": [
            "Market Researcher",
            "Target Audience Analyst",
            "Content Writer",
            "Campaign Manager",
        ],
        "tasks": [
            "Generate Marketing Plan",
            "Research Target Audience",
            "Write Ad Copy",
            "Create Campaign Schedule",
        ],
    },
}

# Create the Streamlit app
st.title("Run crewAI Examples")

# Select an example
selected_example = st.selectbox(
    "Select a crewAI example", list(crewai_examples.keys())
)

# Display example description
st.write(f"**Description:** {crewai_examples[selected_example]['description']}")

# User inputs
inputs = {}
for task in crewai_examples[selected_example]["tasks"]:
    input_label = f"Input for {task}:"
    if task == "Generate Marketing Plan":
        inputs[task] = st.text_area(
            input_label,
            value="""
                Product: AI-powered Marketing Assistant
                Campaign Goals: Increase brand awareness and generate leads
                Budget: $10,000
                Timeline: 3 months
                """,
        )
    elif task == "Research Target Audience":
        inputs[task] = st.text_area(
            input_label,
            value="""
                Describe the ideal customer for an AI-powered Marketing Assistant.
                """,
        )
    elif task == "Write Ad Copy":
        inputs[task] = st.text_area(
            input_label,
            value="""
                Write compelling ad copy for an AI-powered Marketing Assistant 
                targeting marketing professionals. 
                """,
        )
    elif task == "Create Campaign Schedule":
        inputs[task] = st.text_area(
            input_label,
            value="""
                Create a 3-month campaign schedule outlining the key activities 
                for promoting an AI-powered Marketing Assistant.
                """,
        )
    else:
        inputs[task] = st.text_area(input_label)


# --- Tool Instantiation ---


# Get API keys from the secrets dictionary
serper_api_key = api_keys.get("serper")
openai_api_key = api_keys.get("openai")


# Instantiate tools using API keys
search_tool = SerperDevTool(api_key=serper_api_key)
file_read_tool = FileReadTool()
file_write_tool = FileWriteTool()

# Instantiate ChromaDB client
chroma_client = chromadb.Client()  # Create a ChromaDB client instance


# Run the selected example
if st.button("Run Example"):
    if not serper_api_key or not openai_api_key:
        st.error("Please enter both Serper and OpenAI API keys.")
    else:
        # Create agents dynamically based on selected example
        agents = []
        for agent_role in crewai_examples[selected_example]["agents"]:
            if agent_role == "Market Researcher":
                agents.append(
                    Agent(
                        role=agent_role,
                        goal=f"Perform {agent_role} tasks.",
                        tools=[search_tool],
                    )
                )
            elif agent_role == "Content Writer":
                agents.append(
                    Agent(
                        role=agent_role,
                        goal=f"Perform {agent_role} tasks.",
                        tools=[file_read_tool],
                    )
                )
            elif agent_role == "Campaign Manager":
                agents.append(
                    Agent(
                        role=agent_role,
                        goal=f"Perform {agent_role} tasks.",
                        tools=[file_write_tool],
                    )
                )
            else:
                agents.append(
                    Agent(role=agent_role, goal=f"Perform {agent_role} tasks.")
                )

        # Create tasks dynamically based on selected example and user inputs
        tasks = []
        for task_name, user_input in inputs.items():
            tasks.append(
                Task(
                    description=f"{task_name}: {user_input}",
                    agent=agents[
                        crewai_examples[selected_example]["agents"].index(
                            agent_role
                        )
                    ],
                )
            )

        # Instantiate the crew with a sequential process
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            config={"openai_api_key": openai_api_key},
            memory=True,  # Enable CrewAI memory
            embedder={
                "provider": "chroma",
                "config": {"client": chroma_client},  # Pass the client
            },
        )

        # Kick off the crew
        try:
            with st.spinner("Running CrewAI..."):
                result = crew.kickoff()

            # Display the results
            st.write("**Results:**")
            st.write(result)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
