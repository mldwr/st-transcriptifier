import streamlit as st
import youtube_transcript_api

st.title("Youtube Transcript Downloader")

url = st.text_input("Enter the YouTube video URL:")

if url:
    try:
        transcript = youtube_transcript_api.get_transcript(url)
        transcript = [f"{row['start']} - {row['text']}" for row in transcript]
        st.write("\n".join(transcript))
    except Exception as e:
        st.write("Error:", e)
