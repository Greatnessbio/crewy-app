import streamlit as st
import requests
import json
from streamlit.logger import get_logger
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

LOGGER = get_logger(__name__)

def load_api_keys():
    try:
        return {
            "openrouter": st.secrets["secrets"]["openrouter_api_key"],
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
    llm = ChatOpenAI(model="anthropic/claude-3-sonnet-20240229", api_key=api_keys["openrouter"])

    website_analyzer = Agent(
        role="Website Analyzer",
        goal="Analyze competitor websites for structure, content, and SEO elements",
        backstory="Expert in web analysis and SEO best practices",
        llm=llm
    )

    seo_analyst = Agent(
        role="SEO Analyst",
        goal="Analyze competitor SEO strategies and performance",
        backstory="Experienced SEO professional with deep knowledge of search engine algorithms",
        llm=llm
    )

    social_media_analyst = Agent(
        role="Social Media Analyst",
        goal="Analyze competitor social media presence and strategy, focusing on LinkedIn",
        backstory="Social media expert with a focus on B2B platforms",
        llm=llm
    )

    content_strategist = Agent(
        role="Content Strategist",
        goal="Analyze competitor content strategies and identify opportunities",
        backstory="Experienced content marketer with a knack for identifying trends",
        llm=llm
    )

    ppc_analyst = Agent(
        role="PPC and Ad Analyst",
        goal="Analyze competitor PPC and advertising strategies",
        backstory="Digital advertising expert with experience in multiple platforms",
        llm=llm
    )

    return [website_analyzer, seo_analyst, social_media_analyst, content_strategist, ppc_analyst]

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
                    
                    # Create tasks for agents
                    tasks = [
                        Task(
                            description="Analyze the company's LinkedIn profile and provide insights",
                            agent=agents[2],  # Social Media Analyst
                            expected_output="A comprehensive analysis of the company's LinkedIn presence"
                        ),
                        Task(
                            description="Analyze the company's recent LinkedIn posts and engagement",
                            agent=agents[2],  # Social Media Analyst
                            expected_output="An analysis of post frequency, content types, and engagement rates"
                        ),
                        # Add more tasks for other agents here
                    ]

                    # Create and run the crew
                    crew = Crew(
                        agents=agents,
                        tasks=tasks,
                        verbose=2,
                        process=Process.sequential
                    )

                    result = crew.kickoff()
                    
                    st.subheader("Analysis Results")
                    st.write(result)

                    # Display raw data in expanders
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
