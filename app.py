from youtube_transcript_api import YouTubeTranscriptApi as yta
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled
import streamlit as st
from pytube import YouTube
import pandas as pd


def get_id_from_link(link):
    video_id = ""

    if "v=" in link:
        video_id = link.split("v=")[1].split("&")[0]
        return video_id
    elif len(link)==11:
        return link
    else:
        return "Error: Invalid Link."

st.title("Transcriptifier")
st.subheader("Youtube Transcript Downloader")

example_urls = [
    'https://www.youtube.com/watch?v=8uQDDUfGNPA', # blog
    'https://www.youtube.com/watch?v=ofZEo0Rzo5s', # h-educate
    'https://www.youtube.com/watch?v=ReHGSGwV4-A', #wholesale ted
    'https://www.youtube.com/watch?v=n8JHnLgodRI', #kevindavid
    'https://www.youtube.com/watch?v=6MI0f6YjJIk', # Nicholas
    'https://www.youtube.com/watch?v=bj9snrsSook', #Geldschnurrbart
    'https://www.youtube.com/watch?v=lCnHfTHkhbE', #fcc tutorial
    'https://www.youtube.com/watch?v=0kJz0q0pvgQ&feature=youtu.be' # fcc
]


select_examples = st.selectbox(label="Choose an example",options=example_urls)
url = st.text_input("Enter the YouTube video URL:", value=select_examples)

if url:
    video_id = get_id_from_link(url)
    
    transcript_list = yta.list_transcripts(video_id)
    transcript_raw = None

    try:
        transcript_raw = transcript_list.find_transcript(['en']).fetch()
    except NoTranscriptFound as e:
        for transcript in transcript_list:
            transcript_raw = transcript.translate('en').fetch()
            st.write('Transcript translated from ', transcript.language)
    except Exception as e:
        st.write("Error:", e)


    transcript_text = '\n'.join([i['text'].replace('\n',' ') for i in transcript_raw])


yt = YouTube(url)
data = {'Video ID': [video_id],
        'Author': [yt.author], 
        'Title': [yt.title]}
df = pd.DataFrame(data)
df.set_index('Video ID', inplace=True)
st.table(df)
yt_img = f'http://img.youtube.com/vi/{video_id}/mqdefault.jpg'
st.image(yt_img)


with st.expander('Preview Transcript'):
    st.code(transcript_text, language=None)
st.download_button('Download Transcript', transcript_text)



