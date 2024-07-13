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

def get_company_info(company_url, rapidapi_key):
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
        LOGGER.error(f"Company info API request failed: {e}")
        st.error("Failed to fetch company information. Please try again later.")
    return None

def get_company_posts(company_url, rapidapi_key):
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
        LOGGER.error(f"Company posts API request failed: {e}")
        st.error("Failed to fetch company posts. Please try again later.")
    return None

def analyze_text(text, prompt, api_key):
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "anthropic/claude-3-sonnet-20240229",
                "messages": [
                    {"role": "system", "content": "You are an expert in content analysis and creation."},
                    {"role": "user", "content": prompt + "\n\n" + text}
                ]
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.RequestException as e:
        LOGGER.error(f"OpenRouter API request failed: {e}")
        return f"Error: Failed to generate analysis. Please try again later. Details: {str(e)}"
    except (KeyError, IndexError, ValueError) as e:
        LOGGER.error(f"Error processing OpenRouter API response: {e}")
        return f"Error: Failed to process the generated content. Please try again. Details: {str(e)}"

def main_app():
    st.title("LinkedIn Company Analysis")

    api_keys = load_api_keys()
    if not api_keys:
        return

    company_url = st.text_input("Enter LinkedIn Company URL:")

    if st.button("Analyze Company"):
        if company_url:
            with st.spinner("Fetching company information..."):
                company_info = get_company_info(company_url, api_keys["rapidapi"])
                if company_info:
                    st.success("Company information fetched successfully!")
                    st.json(company_info)
                else:
                    st.error("Failed to fetch company information. Please try again.")
                    return

            with st.spinner("Fetching company posts..."):
                company_posts = get_company_posts(company_url, api_keys["rapidapi"])
                if company_posts:
                    st.success("Company posts fetched successfully!")
                    st.json(company_posts)
                else:
                    st.error("Failed to fetch company posts. Please try again.")
                    return

            with st.spinner("Analyzing company profile..."):
                profile_analysis = analyze_text(
                    json.dumps(company_info),
                    "Analyze the company's LinkedIn profile based on the provided data.",
                    api_keys["openrouter"]
                )
                st.subheader("Company Profile Analysis")
                st.write(profile_analysis)

            with st.spinner("Analyzing company posts..."):
                posts_analysis = analyze_text(
                    json.dumps(company_posts),
                    "Analyze the company's LinkedIn posts based on the provided data.",
                    api_keys["openrouter"]
                )
                st.subheader("Company Posts Analysis")
                st.write(posts_analysis)

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
