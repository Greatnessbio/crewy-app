import streamlit as st
import assemblyai as aai
import requests
import json
import os

# Function to call OpenRouter API
@st.cache_data
def summarize_with_openrouter(transcript, api_key):
    YOUR_SITE_URL = "https://your-app-url.com"  # Replace with your actual URL
    YOUR_APP_NAME = "Transcription Analyzer"  # Replace with your app name

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": YOUR_SITE_URL,
            "X-Title": YOUR_APP_NAME,
        },
        json={
            "model": "anthropic/claude-3-sonnet",
            "messages": [
                {"role": "system", "content": "You are an AI assistant that summarizes transcripts and extracts key information into a table."},
                {"role": "user", "content": f"Please summarize the following transcript and extract key information into a table:\n\n{transcript}"}
            ]
        }
    )
    return response.json()['choices'][0]['message']['content']

# Initialize session state
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Streamlit app
st.set_page_config(page_title="Audio Transcription and Analysis", layout="wide")

st.title("Audio Transcription and Analysis with AssemblyAI and OpenRouter")

# Sidebar for API keys
with st.sidebar:
    st.header("API Keys")
    assemblyai_api_key = st.text_input("Enter your AssemblyAI API key:", type="password")
    openrouter_api_key = st.text_input("Enter your OpenRouter API key:", type="password")

# Main content
if assemblyai_api_key and openrouter_api_key:
    aai.settings.api_key = assemblyai_api_key

    # File uploader
    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None:
        st.audio(uploaded_file)

        # Transcription options
        st.subheader("Transcription and Analysis Options")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            speaker_labels = st.checkbox("Enable Speaker Diarization", help="Detect and label different speakers in the audio")
            sentiment_analysis = st.checkbox("Enable Sentiment Analysis", help="Detect the sentiment of each spoken sentence")
        with col2:
            topic_detection = st.checkbox("Enable Topic Detection", help="Identify different topics in the transcript")
            entity_detection = st.checkbox("Enable Entity Detection", help="Identify and categorize key information")
        with col3:
            auto_chapters = st.checkbox("Enable Auto Chapters", help="Summarize audio data over time into chapters")
            key_phrases = st.checkbox("Enable Key Phrases", help="Identify significant words and phrases")

        if st.button("Transcribe and Analyze"):
            with st.spinner("Processing..."):
                try:
                    transcriber = aai.Transcriber()
                    
                    config = aai.TranscriptionConfig(
                        speaker_labels=speaker_labels,
                        sentiment_analysis=sentiment_analysis,
                        iab_categories=topic_detection,
                        entity_detection=entity_detection,
                        auto_chapters=auto_chapters,
                        auto_highlights=key_phrases
                    )
                    
                    # Save uploaded file temporarily and get its path
                    with open(uploaded_file.name, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    transcript = transcriber.transcribe(uploaded_file.name, config)

                    # Store transcript in session state
                    st.session_state.transcript = transcript.text

                    # OpenRouter summarization
                    st.session_state.summary = summarize_with_openrouter(transcript.text, openrouter_api_key)

                    st.success("Transcription and analysis completed!")
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                
                finally:
                    # Clean up the temporary file
                    if os.path.exists(uploaded_file.name):
                        os.remove(uploaded_file.name)

    # Display results
    if st.session_state.transcript:
        st.subheader("Transcription Result")
        with st.expander("Show/Hide Transcript", expanded=True):
            st.write(st.session_state.transcript)
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download Raw Transcript",
                data=st.session_state.transcript,
                file_name="raw_transcript.txt",
                mime="text/plain"
            )
        with col2:
            if st.session_state.summary:
                st.download_button(
                    label="Download Summary",
                    data=st.session_state.summary,
                    file_name="summary.txt",
                    mime="text/plain"
                )

        # Display analysis results
        if st.session_state.summary:
            st.subheader("Summary and Key Information")
            st.write(st.session_state.summary)

        if speaker_labels and hasattr(transcript, 'utterances'):
            st.subheader("Speaker Diarization")
            for utterance in transcript.utterances:
                st.write(f"Speaker {utterance.speaker}: {utterance.text}")

        if sentiment_analysis and hasattr(transcript, 'sentiment_analysis'):
            st.subheader("Sentiment Analysis")
            for result in transcript.sentiment_analysis:
                st.write(f"Text: {result.text}")
                st.write(f"Sentiment: {result.sentiment}, Confidence: {result.confidence:.2f}")
                st.write(f"Timestamp: {result.start} - {result.end}")
                st.write("---")

        if topic_detection and hasattr(transcript, 'iab_categories'):
            st.subheader("Topic Detection")
            for topic, relevance in transcript.iab_categories.summary.items():
                st.write(f"Topic: {topic}, Relevance: {relevance:.2f}")

        if entity_detection and hasattr(transcript, 'entities'):
            st.subheader("Entity Detection")
            for entity in transcript.entities:
                st.write(f"Text: {entity.text}")
                st.write(f"Entity Type: {entity.entity_type}")
                st.write(f"Timestamp: {entity.start} - {entity.end}")
                st.write("---")

        if auto_chapters and hasattr(transcript, 'chapters'):
            st.subheader("Auto Chapters")
            for chapter in transcript.chapters:
                st.write(f"Time: {chapter.start}-{chapter.end}")
                st.write(f"Headline: {chapter.headline}")
                st.write(f"Summary: {chapter.summary}")
                st.write("---")

        if key_phrases and hasattr(transcript, 'auto_highlights'):
            st.subheader("Key Phrases")
            for result in transcript.auto_highlights.results:
                st.write(f"Phrase: {result.text}")
                st.write(f"Count: {result.count}, Rank: {result.rank:.2f}")
                st.write(f"Timestamps: {result.timestamps}")
                st.write("---")

    # Chat interface
    st.subheader("Chat about the Transcript")
    user_input = st.text_input("Ask a question about the transcript:")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner("Generating response..."):
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "HTTP-Referer": "https://your-app-url.com",
                    "X-Title": "Transcription Analyzer",
                },
                json={
                    "model": "anthropic/claude-3-sonnet",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant. Use the provided transcript to answer questions."},
                        {"role": "user", "content": f"Here's the transcript for context:\n\n{st.session_state.transcript}\n\nNow, please answer the following question: {user_input}"}
                    ] + st.session_state.chat_history
                }
            )
        
        ai_response = response.json()['choices'][0]['message']['content']
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.write(f"You: {message['content']}")
        else:
            st.write(f"AI: {message['content']}")

else:
    st.warning("Please enter both your AssemblyAI and OpenRouter API keys in the sidebar to proceed.")

st.sidebar.markdown("---")
st.sidebar.markdown("Powered by AssemblyAI and OpenRouter")
