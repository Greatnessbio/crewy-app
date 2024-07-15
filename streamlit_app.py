import streamlit as st
import assemblyai as aai

# Streamlit app title
st.title("Audio Transcription with AssemblyAI")

# API key input
api_key = st.text_input("Enter your AssemblyAI API key:", type="password")

if api_key:
    aai.settings.api_key = api_key

    # File uploader
    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None:
        st.audio(uploaded_file)

        # Transcription options
        st.subheader("Transcription Options")
        speaker_labels = st.checkbox("Enable Speaker Diarization")

        if st.button("Transcribe"):
            with st.spinner("Transcribing..."):
                try:
                    transcriber = aai.Transcriber()
                    config = aai.TranscriptionConfig(speaker_labels=speaker_labels)
                    
                    # Save uploaded file temporarily and get its path
                    with open(uploaded_file.name, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    transcript = transcriber.transcribe(uploaded_file.name, config)

                    st.subheader("Transcription Result")
                    st.write(transcript.text)

                    if speaker_labels and transcript.utterances:
                        st.subheader("Speaker Diarization")
                        for utterance in transcript.utterances:
                            st.write(f"Speaker {utterance.speaker}: {utterance.text}")
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                
                finally:
                    # Clean up the temporary file
                    import os
                    if os.path.exists(uploaded_file.name):
                        os.remove(uploaded_file.name)

else:
    st.warning("Please enter your AssemblyAI API key to proceed.")

st.markdown("---")
st.markdown("Powered by AssemblyAI")
