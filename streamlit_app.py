import streamlit as st
import assemblyai as aai
import requests
import json
import os

# Function to call OpenRouter API
def summarize_with_openrouter(transcript):
    OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
    YOUR_SITE_URL = "https://your-app-url.com"  # Replace with your actual URL
    YOUR_APP_NAME = "Transcription Analyzer"  # Replace with your app name

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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

# Streamlit app title
st.title("Audio Transcription and Analysis with AssemblyAI and OpenRouter")

# API key input
api_key = st.text_input("Enter your AssemblyAI API key:", type="password")

if api_key:
    aai.settings.api_key = api_key

    # File uploader
    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None:
        st.audio(uploaded_file)

        # Transcription options
        st.subheader("Transcription and Analysis Options")
        
        speaker_labels = st.checkbox("Enable Speaker Diarization", help="Detect and label different speakers in the audio")
        sentiment_analysis = st.checkbox("Enable Sentiment Analysis", help="Detect the sentiment of each spoken sentence")
        topic_detection = st.checkbox("Enable Topic Detection", help="Identify different topics in the transcript")
        entity_detection = st.checkbox("Enable Entity Detection", help="Identify and categorize key information")
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

                    st.subheader("Transcription Result")
                    st.write(transcript.text)

                    # Download button for raw transcript
                    st.download_button(
                        label="Download Raw Transcript",
                        data=transcript.text,
                        file_name="raw_transcript.txt",
                        mime="text/plain"
                    )

                    # Display results for each selected AI model
                    if speaker_labels and transcript.utterances:
                        st.subheader("Speaker Diarization")
                        for utterance in transcript.utterances:
                            st.write(f"Speaker {utterance.speaker}: {utterance.text}")

                    if sentiment_analysis:
                        st.subheader("Sentiment Analysis")
                        for result in transcript.sentiment_analysis:
                            st.write(f"Text: {result.text}")
                            st.write(f"Sentiment: {result.sentiment}, Confidence: {result.confidence:.2f}")
                            st.write(f"Timestamp: {result.start} - {result.end}")
                            st.write("---")

                    if topic_detection:
                        st.subheader("Topic Detection")
                        for topic, relevance in transcript.iab_categories.summary.items():
                            st.write(f"Topic: {topic}, Relevance: {relevance:.2f}")

                    if entity_detection:
                        st.subheader("Entity Detection")
                        for entity in transcript.entities:
                            st.write(f"Text: {entity.text}")
                            st.write(f"Entity Type: {entity.entity_type}")
                            st.write(f"Timestamp: {entity.start} - {entity.end}")
                            st.write("---")

                    if auto_chapters:
                        st.subheader("Auto Chapters")
                        for chapter in transcript.chapters:
                            st.write(f"Time: {chapter.start}-{chapter.end}")
                            st.write(f"Headline: {chapter.headline}")
                            st.write(f"Summary: {chapter.summary}")
                            st.write("---")

                    if key_phrases:
                        st.subheader("Key Phrases")
                        for result in transcript.auto_highlights.results:
                            st.write(f"Phrase: {result.text}")
                            st.write(f"Count: {result.count}, Rank: {result.rank:.2f}")
                            st.write(f"Timestamps: {result.timestamps}")
                            st.write("---")

                    # OpenRouter summarization
                    st.subheader("OpenRouter Summarization and Key Information")
                    openrouter_output = summarize_with_openrouter(transcript.text)
                    st.write(openrouter_output)

                    # Download button for OpenRouter output
                    st.download_button(
                        label="Download OpenRouter Output",
                        data=openrouter_output,
                        file_name="openrouter_output.txt",
                        mime="text/plain"
                    )

                    # Store the transcript in session state for the chat
                    st.session_state['transcript'] = transcript.text
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                
                finally:
                    # Clean up the temporary file
                    if os.path.exists(uploaded_file.name):
                        os.remove(uploaded_file.name)

        # Chat interface
        st.subheader("Chat about the Transcript")
        if 'transcript' in st.session_state:
            if 'messages' not in st.session_state:
                st.session_state['messages'] = [{"role": "system", "content": "You are a helpful assistant. Use the provided transcript to answer questions."}]

            for message in st.session_state['messages']:
                if message['role'] != 'system':
                    st.write(f"{'You' if message['role'] == 'user' else 'AI'}: {message['content']}")

            user_input = st.text_input("Ask a question about the transcript:")
            if user_input:
                st.session_state['messages'].append({"role": "user", "content": user_input})
                
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
                        "HTTP-Referer": "https://your-app-url.com",
                        "X-Title": "Transcription Analyzer",
                    },
                    json={
                        "model": "anthropic/claude-3-sonnet",
                        "messages": st.session_state['messages'] + [{"role": "user", "content": f"Here's the transcript for context:\n\n{st.session_state['transcript']}\n\nNow, please answer the following question: {user_input}"}]
                    }
                )
                
                ai_response = response.json()['choices'][0]['message']['content']
                st.session_state['messages'].append({"role": "assistant", "content": ai_response})
                st.write(f"AI: {ai_response}")

else:
    st.warning("Please enter your AssemblyAI API key to proceed.")

st.markdown("---")
st.markdown("Powered by AssemblyAI and OpenRouter")
