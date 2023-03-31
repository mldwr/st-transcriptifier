from youtube_transcript_api import YouTubeTranscriptApi as yta
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled
import streamlit as st
from pytube import YouTube
from pytube import Channel
from pytube import exceptions
import pandas as pd
import scrapetube
import requests
import datetime 

def update_param():
    video_id = get_id_from_link(st.session_state.s_vid) 
    st.experimental_set_query_params(vid=video_id)

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
    'https://www.youtube.com/watch?v=nr4kmlTr9xw&list=WL&index=4', # Linus
    'https://www.youtube.com/watch?v=64Izfm24FKA', # Yannic
    'https://www.youtube.com/watch?v=Mt1P7p9HmkU', # Fogarty
    'https://www.youtube.com/watch?v=bj9snrsSook', #Geldschnurrbart
    'https://www.youtube.com/watch?v=0kJz0q0pvgQ&feature=youtu.be', # fcc
    'https://www.youtube.com/watch?v=yqkISICHH-U&t=10s',
    'https://www.youtube.com/watch?v=uKyojQjbx4c',
    'https://www.youtube.com/watch?v=3l16wCsDglU',
    'https://www.youtube.com/watch?v=gNRGkMeITVU&list=WL&index=28', # iman
    'https://www.youtube.com/watch?v=vAuQuL8dlXo&list=WL&index=30', #ghiorghiu
    'https://www.youtube.com/watch?v=5scEDopRAi0&list=WL&index=29&t=71s', #infohaus
    'https://www.youtube.com/watch?v=lCnHfTHkhbE', #fcc tutorial
    'https://www.youtube.com/watch?v=QI2okshNv_4'
]


# Initialization
if 's_vid' not in st.session_state:
    st.session_state.s_vid = ''

vid_param = st.experimental_get_query_params().get("vid")

if st.session_state.s_vid:
    se_vid = get_id_from_link(st.session_state.s_vid) 

if vid_param:
    pa_vid = get_id_from_link("".join(vid_param)) 

if vid_param == None:
    st.session_state.s_vid = example_urls[0]
    
pa_url=None
if vid_param and vid_param != st.session_state.s_vid:
    pa_url = get_link_from_id("".join(vid_param))
    st.session_state.s_vid = pa_url
    if pa_url not in example_urls:
        example_urls.append(pa_url)

select_examples = st.selectbox(label="Choose an example",options=example_urls, key='s_vid', on_change=update_param)
url = st.text_input("Enter the YouTube video URL:", value=pa_url if pa_url else select_examples)


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

    #if 'transcript' not in st.session_state:
    #st.session_state['transcript'] = transcript_text


########################
# Load the data for a given video
########################

yt = YouTube(get_link_from_id(url))

yt_img = f'http://img.youtube.com/vi/{video_id}/mqdefault.jpg'
#yt_img_markdown ="[![Image_with_Link]("+yt_img+")]("+url+")"
yt_img_html = '<img src='+yt_img+' width="250" height="150" />'
yt_img_html_link = '<a href='+url+'>'+yt_img_html+'</a>'

try:
    data = {'Video':[yt_img_html_link],
            'Author': [yt.author],
            'Title': [yt.title],
            'Published': [yt.publish_date.strftime('%B %d, %Y')],
            'Views':['{:,}'.format(yt.views).replace(',', '\'')],
            'Length (min)':[int(yt.length/60)]}
except exceptions.PytubeError:
    st.error('This is some random error, please restart the application.', icon="🚨")
    st.stop()

df = pd.DataFrame(data)
st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)
st.write("")


########################
# Load Author Keywords, that are not viewable by users
########################

df = pd.DataFrame(yt.keywords, columns=['Authors Keywords'])
st.write(df)



########################
# Display the transcript along with the download button
########################

with st.expander('Preview Transcript'):
    st.code(transcript_text, language=None)
st.download_button('Download Transcript', transcript_text)

########################
# API Call to deeppunkt-gr
########################

def get_punctuated_text(raw_text):
    response = requests.post("https://wldmr-deeppunct-gr.hf.space/run/predict", json={
        "data": [
            ["sentences"],
            raw_text,
        ]})
    
    if response.status_code == 504:
        st.error('The API call took too long, the server answered with a timeout, please try again.', icon="🚨")
        st.stop()
    elif response.status_code != 200:
        st.error('The API replyed with an error, please try again: '+str(response.status_code), icon="🚨")
        st.stop()
    st.session_state['punkt'] = response.json()


st.subheader("Restore Punctuations of Transcript")

if st.button('Load Punctuated Transcript'):
    with st.spinner('Loading Punctuation...'):
        if 'punkt' not in st.session_state:
            get_punctuated_text(transcript_text)
    st.write('Load time: '+str(round(st.session_state.punkt['duration'],1))+' sec')
    with st.expander('Preview Transcript'):
        st.code(st.session_state.punkt['data'][0], language=None)

########################
# API Call to lexrank-gr
########################

def get_extracted_text(raw_text):
    response = requests.post("https://wldmr-lexrank-gr.hf.space/run/predict", json={
        "data": [
            raw_text,
        ]})
    #response_id = response
    st.session_state['extract'] = response.json()


# TODO: Remove sentences that are smaller than 10 words long
# Remove "um" words from text
st.subheader("Extract Core Sentences from Transcript")

if st.button('Extract Sentences'):
    with st.spinner('Loading Punctuation (Step 1/2)...'):
        if 'punkt' not in st.session_state:
            get_punctuated_text(transcript_text)
    with st.spinner('Loading Extractions (Step 2/2)...'):
        if 'extract' not in st.session_state:
            get_extracted_text(st.session_state.punkt['data'][0])
    st.write('Load time: '+str(round(st.session_state.extract['duration'],1))+' sec')
    data = {'Words':[int(st.session_state.extract['data'][1])],
            'Sentences': [int(st.session_state.extract['data'][2])],
            'Characters': [int(st.session_state.extract['data'][3])],
            'Tokens':[int(st.session_state.extract['data'][4])]}
    df = pd.DataFrame(data)
    st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)
    st.write("")
    with st.expander('Preview Transcript'):
        st.code(st.session_state.extract['data'][0], language=None)


#######################
# API Call to summarymachine
########################

def get_summarized_text(raw_text):
    response = requests.post("https://wldmr-summarymachine.hf.space/run/predict", json={
        "data": [
            raw_text,
        ]})
    #response_id = response
    if response.status_code == 504:
        raise "Error: Request took too long (>60sec), please try a shorter text."
    return response.json()

st.subheader("Summarize Extracted Sentences with Flan-T5-large")

if st.button('Summarize Sentences'):
    command = 'Summarize the transcript in one sentence:\n\n'
    with st.spinner('Loading Punctuation (Step 1/3)...'):
        if 'punkt' not in st.session_state:
            get_punctuated_text(transcript_text)
    with st.spinner('Loading Extraction (Step 2/3)...'):
        if 'extract' not in st.session_state:
            get_extracted_text(st.session_state.punkt['data'][0])
    with st.spinner('Loading Summary (Step 3/3)...'):
        summary_text = get_summarized_text(command+st.session_state.extract['data'][0])
    st.write('Load time: '+str(round(summary_text['duration'],1))+' sec')
    with st.expander('Preview Transcript'):
        st.write(summary_text['data'][0], language=None)

########################
# Channel
########################


st.subheader("Other Videos of the Channel")


#@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df = [input_df.loc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df


if st.button('Load all Videos'):
    ytc = Channel(yt.channel_url)

    with st.spinner('Loading...'):
        videos = scrapetube.get_channel(yt.channel_id)

    vids_thumbnails = []
    vids_videoIds = []
    vids_titles = []
    vids_lengths = []
    vids_published= []
    vids_views= []
    for video in videos:
        vids_video_id = video['videoId']
        vids_url = 'https://www.youtube.com/watch?v='+vids_video_id

        yt_img = f'http://img.youtube.com/vi/{vids_video_id}/mqdefault.jpg'
        yt_img_html = '<img src='+yt_img+' width="250" height="150" />'
        yt_img_html_link = '<a href='+vids_url+'>'+yt_img_html+'</a>'
        vids_thumbnails.append(yt_img_html_link)
        
        vids_video_id_link = '<a target="_self" href="/?vid='+vids_video_id+'">'+vids_video_id+'</a>'
        vids_videoIds.append(vids_video_id_link)

        dict_string = video['title']
        title_value = dict_string["runs"][0]["text"]
        vids_titles.append(title_value)
        vids_lengths.append(video['lengthText']['simpleText'])
        vids_published.append(video['publishedTimeText']['simpleText'])
        vids_views.append(video['viewCountText']['simpleText'])

    df_videos = {'Video': vids_thumbnails,
                'Transcript':vids_videoIds,
                'Title':vids_titles,
                'Length':vids_lengths,
                'Published':vids_published,
                'Views':vids_views}

    st.write('Number of videos:',len(vids_videoIds))
    #st.table(df_videos)

    dataset = pd.DataFrame(df_videos)
    st.markdown(dataset.style.hide(axis="index").to_html(), unsafe_allow_html=True)



###############
# End of File #
###############
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

