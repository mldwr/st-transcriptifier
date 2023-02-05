from youtube_transcript_api import YouTubeTranscriptApi as yta
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled
import streamlit as st
from pytube import YouTube
import pandas as pd

def update_param():
    #vid = get_id_from_link("".join(vid_param)) 
    video_id = get_id_from_link(st.session_state.s_vid) 
    st.experimental_set_query_params(vid=video_id)
    #st.experimental_set_query_params(vid=st.session_state.s_vid)
    #st.code('vid: '+st.session_state.s_vid)
    st.code('update_param: '+video_id)

def get_link_from_id(video_id):
    if "v=" not in video_id:
        return 'https://www.youtube.com/watch?v='+video_id
    else:
        return video_id


def get_id_from_link(link):
    if "v=" in link:
        return link.split("v=")[1].split("&")[0]
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
    'https://www.youtube.com/watch?v=0kJz0q0pvgQ&feature=youtu.be' # fcc
]

# https://www.youtube.com/watch?v=yqkISICHH-U&t=10s
# https://www.youtube.com/watch?v=uKyojQjbx4c
# https://www.youtube.com/watch?v=3l16wCsDglU
# 'https://www.youtube.com/watch?v=lCnHfTHkhbE', #fcc tutorial

# Initialization
if 's_vid' not in st.session_state:
    st.session_state.s_vid = ''

vid_param = st.experimental_get_query_params().get("vid")

if st.session_state.s_vid:
    se_vid = get_id_from_link(st.session_state.s_vid) 
    st.code('se '+se_vid)
else:
    st.code('st.session_state.s_vid empty')

if vid_param:
    pa_vid = get_id_from_link("".join(vid_param)) 
#     #st.experimental_set_query_params(vid=video_id)
    st.code('pa '+pa_vid)
else:
    st.code('vid_param empty')

if vid_param == None:
    st.session_state.s_vid = example_urls[0]
    #st.session_state.s_vid = get_id_from_link(example_urls[0])
    st.code('set example_urls[0] to '+example_urls[0])
    
# # If the parameter was already seen, then empty it
# # only use the parameter if has changed
# if st.session_state.s_vid and st.session_state.s_vid == vid_param:
#     st.session_state.s_vid = ''
# else:
#     st.session_state.s_vid = vid_param

# st.code(st.session_state.s_vid)

pa_url=None
if vid_param and vid_param != st.session_state.s_vid:
    pa_url = get_link_from_id("".join(vid_param))
    st.session_state.s_vid = pa_url
    example_urls.append(pa_url)
    st.code('paurl '+pa_url)

select_examples = st.selectbox(label="Choose an example",options=example_urls, key='s_vid', on_change=update_param)
url = st.text_input("Enter the YouTube video URL:", value=pa_url if pa_url else select_examples)
#url = st.text_input("Enter the YouTube video URL:", value=select_examples)


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

# PytubeError: Exception while accessing title of https://youtube.com/watch?v=bj9snrsSook. Please file a bug report at https://github.com/pytube/pytube

yt = YouTube(get_link_from_id(url))
data = {'Video ID': [video_id],
        'Author': [yt.author], 
        'Title': [yt.title]}
df = pd.DataFrame(data)
df.set_index('Video ID', inplace=True)
st.table(df)
yt_img = f'http://img.youtube.com/vi/{video_id}/mqdefault.jpg'
st.markdown("[![Image_with_Link]("+yt_img+")]("+url+")")

with st.expander('Preview Transcript'):
    st.code(transcript_text, language=None)
st.download_button('Download Transcript', transcript_text)



