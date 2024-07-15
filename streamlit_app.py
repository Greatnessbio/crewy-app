import streamlit as st
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch

# Load the Whisper model and processor
processor = WhisperProcessor.from_pretrained("openai/whisper-base")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base")

def transcribe_audio(audio_file):
    # Load the audio file
    audio, sr = torchaudio.load(audio_file)

    # Preprocess the audio
    inputs = processor(audio, sampling_rate=sr, return_tensors="pt")

    # Run the model
    generated_ids = model.generate(**inputs)
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return transcription

def main():
    st.title("Audio Transcription App")
    st.write("Upload an audio file and it will be transcribed using the Whisper model.")

    audio_file = st.file_uploader("Upload your audio file", type=["wav", "mp3", "ogg"])
    if audio_file is not None:
        # Transcribe the audio file
        transcription = transcribe_audio(audio_file)

        # Display the transcription
        st.header("Transcription")
        st.write(transcription)

if __name__ == "__main__":
    main()
