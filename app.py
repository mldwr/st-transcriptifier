from youtube_transcript_api import YouTubeTranscriptApi as yta
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled
import streamlit as st
from pytube import YouTube
from pytube import Channel
import pandas as pd
import scrapetube

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

# PytubeError: Exception while accessing title of https://youtube.com/watch?v=bj9snrsSook. Please file a bug report at https://github.com/pytube/pytube

yt = YouTube(get_link_from_id(url))


yt_img = f'http://img.youtube.com/vi/{video_id}/mqdefault.jpg'
#yt_img_markdown ="[![Image_with_Link]("+yt_img+")]("+url+")"
yt_img_html = '<img src='+yt_img+' width="250" height="150" />'
yt_img_html_link = '<a href='+url+'>'+yt_img_html+'</a>'

data = {'Video':[yt_img_html_link],
        'Author': [yt.author],
        'Title': [yt.title],
        'Published': [yt.publish_date],
        'Views':[yt.views]}
df = pd.DataFrame(data)
st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)
st.write("")


df = pd.DataFrame(yt.keywords, columns=['Authors Keywords'])
st.write(df)

with st.expander('Preview Transcript'):
    st.code(transcript_text, language=None)
st.download_button('Download Transcript', transcript_text)

########################
# Channel


st.subheader("Other Videos of the Channel")


#@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df = [input_df.loc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df

ytc = Channel(yt.channel_url)

videos = scrapetube.get_channel(yt.channel_id)
#st.dataframe(videos)

vids_thumbnails = []
vids_videoIds = []
vids_titles = []
vids_lengths = []
vids_published= []
vids_views= []
for video in videos:
  vids_video_id = video['videoId']
  
  yt_img = f'http://img.youtube.com/vi/{vids_video_id}/mqdefault.jpg'
  yt_img_html = '<img src='+yt_img+' width="250" height="150" />'
  yt_img_html_link = '<a href='+url+'>'+yt_img_html+'</a>'
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

# top_menu = st.columns(3)
# with top_menu[0]:
#     sort = st.radio("Sort Data", options=["Yes", "No"], horizontal=1, index=1)
# if sort == "Yes":
#     with top_menu[1]:
#         sort_field = st.selectbox("Sort By", options=dataset.columns)
#     with top_menu[2]:
#         sort_direction = st.radio(
#             "Direction", options=["??????", "??????"], horizontal=True
#         )
#     dataset = dataset.sort_values(
#         by=sort_field, ascending=sort_direction == "??????", ignore_index=True
#     )
# pagination = st.container()

# bottom_menu = st.columns((4, 1, 1))
# with bottom_menu[2]:
#     batch_size = st.selectbox("Page Size", options=[10, 25, 50, 100])
# with bottom_menu[1]:
#     total_pages = (
#         int(len(dataset) / batch_size) if int(len(dataset) / batch_size) > 0 else 1
#     )
#     current_page = st.number_input(
#         "Page", min_value=1, max_value=total_pages, step=1
#     )
# with bottom_menu[0]:
#     st.markdown(f"Page **{current_page}** of **{total_pages}** ")

# pages = split_frame(dataset, batch_size)
# pagination.table(data=pages[current_page - 1])
# #pagination.dataframe(data=pages[current_page - 1], use_container_width=True)


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

