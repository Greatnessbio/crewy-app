import streamlit as st
import requests
from streamlit.logger import get_logger
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

LOGGER = get_logger(__name__)

def load_api_keys():
    try:
        return {
            "openai": st.secrets["secrets"]["openai_api_key"],
            "rapidapi": st.secrets["secrets"]["rapidapi_key"]
        }
    except KeyError as e:
        st.error(f"{e} API key not found in secrets.toml. Please add it.")
        return None

def load_users():
    return st.secrets["users"]

def login(username, password):
    users = load_users()
    if username in users and users[username] == password:
        return True
    return False

def get_linkedin_company_data(company_url, rapidapi_key):
    url = "https://linkedin-data-scraper.p.rapidapi.com/company_pro"
    payload = {"link": company_url}
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "linkedin-data-scraper.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        LOGGER.error(f"LinkedIn company data request failed: {e}")
        st.error("Failed to fetch company information. Please try again.")
    return None

def get_linkedin_company_posts(company_url, rapidapi_key):
    url = "https://linkedin-data-scraper.p.rapidapi.com/company_updates"
    payload = {
        "company_url": company_url,
        "posts": 20,
        "comments": 10,
        "reposts": 10
    }
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "linkedin-data-scraper.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        LOGGER.error(f"LinkedIn company posts request failed: {e}")
        st.error("Failed to fetch company posts. Please try again.")
    return None

def create_agents(api_keys):
    llm = ChatOpenAI(model="gpt-4", api_key=api_keys["openai"])

    researcher = Agent(
        role='Senior Research Analyst',
        goal='Discover and analyze company information from LinkedIn',
        backstory="""You're a senior research analyst specializing in company analysis.
        Your expertise lies in extracting valuable insights from company profiles and posts.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    writer = Agent(
        role='Content Strategist',
        goal='Analyze content strategy and provide actionable insights',
        backstory="""You're an experienced content strategist with a knack for understanding
        B2B communication strategies on LinkedIn. Your analyses help companies improve their content.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    return [researcher, writer]

def main_app():
    st.title("Digital Marketing Competitor Analysis Tool")

    api_keys = load_api_keys()
    if not api_keys:
        return

    agents = create_agents(api_keys)

    company_url = st.text_input("Enter competitor's LinkedIn Company URL:")
    
    if st.button("Analyze Competitor"):
        if company_url:
            with st.spinner("Analyzing competitor data..."):
                company_data = get_linkedin_company_data(company_url, api_keys["rapidapi"])
                company_posts = get_linkedin_company_posts(company_url, api_keys["rapidapi"])

                if company_data and company_posts:
                    st.success("Data fetched successfully!")
                    
                    research_task = Task(
                        description=f"Analyze the LinkedIn profile and recent posts of the company at {company_url}. Focus on their industry positioning, key offerings, and overall online presence.",
                        agent=agents[0]
                    )

                    content_task = Task(
                        description="Based on the research, provide a detailed content strategy analysis. Include insights on post frequency, engagement rates, content themes, and areas for improvement.",
                        agent=agents[1]
                    )

                    crew = Crew(
                        agents=agents,
                        tasks=[research_task, content_task],
                        verbose=2,
                        process=Process.sequential
                    )

                    result = crew.kickoff()
                    
                    st.subheader("Analysis Results")
                    st.write(result)

                    with st.expander("Raw Company Data"):
                        st.json(company_data)
                    with st.expander("Raw Company Posts"):
                        st.json(company_posts)
                else:
                    st.error("Failed to fetch company data. Please try again.")
        else:
            st.warning("Please enter a LinkedIn Company URL.")

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login(username, password):
            st.session_state.logged_in = True
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def display():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
    else:
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
        else:
            main_app()

if __name__ == "__main__":
    display()
