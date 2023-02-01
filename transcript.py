from youtube_transcript_api import YouTubeTranscriptApi
import re
from PIL import Image
import base64


#transcript_list = YouTubeTranscriptApi.list_transcripts('ReHGSGwV4-A')
#transcript = transcript_list.find_transcript(['en','de'])

def get_id_from_link(link):
    video_id = ""

    if "v=" in link:
        video_id = link.split("v=")[1].split("&")[0]
        return video_id
    elif len(link)==11:
        return link
    else:
        return "Error: Invalid Link."
 

# step 1: download the json transcript for youtube video
def get_json_transcript(video_id,rpunkt_switch):

    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    # get the auto-generated english text
    # if it is not available translate to en
    raw_transcript = 'empty'
    type_transcript = []
    if rpunkt_switch:
        try:
            transcript = transcript_list.find_generated_transcript(['en'])
            raw_transcript = transcript.fetch()
            type_transcript = ['en','generated']
        except:
            transcript = transcript_list.find_transcript(['de'])
            raw_transcript = transcript.translate('en').fetch()
            type_transcript = ['en','translated']
    else:
        transcript = transcript_list.find_transcript(['en','de'])
        raw_transcript = transcript.fetch()
        type_transcript = ['den','manual']

    return raw_transcript, type_transcript

# step 2: extract timestamps from json transcript
def get_timestamps(transcript_raw):
    transcript_timestamps = '\n'.join([str(i['start']) for i in transcript_raw])
    return transcript_timestamps.split('\n')

# step 3: extract text from transcript
def get_caption(transcript_raw):
    transcript_text = '\n'.join([i['text'].replace('\n',' ') for i in transcript_raw])
    return transcript_text

def replacePunctuatedText(raw_transcript, caption):
    list_caption = caption.split('\n')
    pnct_raw_transcript = raw_transcript

    for (idx, line) in enumerate(pnct_raw_transcript):
        line['text']=list_caption[idx]
    
    return pnct_raw_transcript

def getSentences(raw_transcript):
    # walk over each frame and extract the time stamp and the text 
    # the time stamp is wrapped in hash tag signs
    frm_cap = ''
    for (idx, line) in enumerate(raw_transcript, start=1):
        frm_cap = frm_cap+' #'+str(idx)+'# '+line['text'].replace('\n',' ').replace('\n',' ')


    dict_sentences = {}
    sentences = frm_cap.strip().split('. ')
    # small sentences that do not have an own frame are dropped
    # sentences that are less than 20 letters large are dropped, too
    # this is useful, so that lexrank does not picks the short sentences
    for idx,item in enumerate(sentences):
        m = re.search(r"#[^#]*#", item)
        if m is not None:
            match = m.group(0)
        frm = match.replace('#','')
        clean_match = re.sub('\s*#[^#]*#\s*',' ',item) + '.'
        if len(clean_match) > 20:
            dict_sentences[frm] = clean_match.strip()
        
    
    return dict_sentences


    # split all sentences into an array
    # remove all timestamps in the middle of the sentences
    # leave only the timestamps at the beginning of each sentence 
    # restore the full-stop sign at the end of each sentence, that was removed in the split step
    #chops = ''
    #for item in sl.strip().split('. '):
    #    chops = chops + re.sub('\s*#[^#]*#\s*',' ',item) + '. '
    #chops

    # remove all remaining hash tags
    #dsl={}
    #for item in chops.split('. #'):
    #    elem= item.split('# ')
    #    idx = elem[0].replace('#','')
    #    sentence = elem[1]+'.'
    #    dsl[idx] = sentence

    #return dsl

def convertToJSON(dsl):
    workdir = './workdir/'
    cnt=1
    json_rows = '['
    for (key,val) in dsl.items():
        image='frame_'+f"{int(cnt):04d}"+'.jpg'

        # open image and convert it to base64 image
        with open(workdir+image, 'rb') as open_file:
             byte_content = open_file.read()
        base64_bytes = base64.b64encode(byte_content)
        base64_string = base64_bytes.decode('utf-8')

        sentence = val 
        row = '{"image_id": "'+str(cnt)+'",'
        row = row + '"timestamp": "'+key+'",'
        row = row + '"image": "'+base64_string+'",'
        row = row + '"caption": "'+sentence+'"},'
        json_rows = json_rows + row
        cnt = cnt+1
    # remove the comma from the last item
    json_rows = json_rows[:-1] + ']'

    return json_rows


def convertToHTML(dsl):
    #workdir = 'file/workdir/'
    workdir = '../workdir/'
    cnt=1
    html_rows = '<table border=1>'
    html_rows = html_rows + '<tr><td>Image Nr.</td><td>Timestamp [sec]</td><td>Image</td><td>Caption</td>'
    for (key,val) in dsl.items():
        image='frame_'+f"{int(cnt):04d}"+'.jpg'
        sentence = val 
        row = '<tr><td>'+str(cnt)+'</td>'
        #row = row +'<td>'+f"{int(key):04d}"+'</td>'
        row = row +'<td>'+key+'</td>'
        row = row +'<td><a href='+workdir+image+'><img src="'+workdir+image+'" width=500></a></td>'
        row = row +'<td>'+sentence+'</td></tr>\n'
        html_rows = html_rows + row
        cnt = cnt+1
    html_rows = html_rows + '</table>'


    filename='./workdir/output.html'
    with open(filename, 'w') as the_file:
        the_file.write(html_rows)

    return html_rows

def getImages(dsl):
    images = []
    workdir = 'workdir/'
    cnt=1
    for (key,val) in dsl.items():
        image='frame_'+f"{int(cnt):04d}"+'.jpg'
        image_path = workdir+image
        pil_im = Image.open(image_path)
        images.append(pil_im)
        cnt=cnt+1

    return images 


# 1.
# dict_sentences contains all sentences with the frame-nr
# list_summary contains the summed sentences
# the task is to find for all summarized sentences the corresponding frame-nr
# 2.
# dict_frame_timestamp contains a mapping of frames to the timestamps
# 3.
# it is used to construct the sum_timestamps list of the timestamps for each summarized sentence
def getTimestampAtFrameFromSummary(raw_transcript, dict_sentences,list_summary):
    dict_summary = {}
    for key, value in dict_sentences.items():
        for sentence in list_summary:
            if str(sentence) in value:
                dict_summary[key]=value

    # sanity check, if the number of summarized sentences was found
    if len(list_summary) != len(dict_summary):
        err_msg = 'Error: Number of summarized sentences '+str(len(list_summary)) +' is not equal to the identified sentences '+str(len(dict_summary))+'.'
        print(err_msg)
        return err_msg

    dict_frame_timestamp = {}
    for (idx, line) in enumerate(raw_transcript, start=1):
        dict_frame_timestamp[str(idx)] = str(line['start'])

    sum_timestamps = []
    for key in dict_summary.keys():
        sum_timestamps.append(dict_frame_timestamp.get(key))

    dict_timestamp_summary = {}
    for (idx,value) in enumerate(list_summary):
        timestamp = sum_timestamps[idx]
        dict_timestamp_summary[timestamp] = str(value)

    return dict_timestamp_summary


def restore_cr(input_text, output_text):
    # restore the carrige returns 
    srt_file = input_text
    punctuated = output_text

    srt_file_strip=srt_file.strip()
    srt_file_sub=re.sub('\s*\n\s*','# ',srt_file_strip)
    srt_file_array=srt_file_sub.split(' ')
    pcnt_file_array=punctuated.split(' ')

    # goal: restore the break points i.e. the same number of lines as the srt file
    # this is necessary, because each line in the srt file corresponds to a frame from the video
    if len(srt_file_array)!=len(pcnt_file_array):
        return "AssertError: The length of the transcript and the punctuated file should be the same: ",len(srt_file_array),len(pcnt_file_array)
    pcnt_file_array_hash = []
    for idx, item in enumerate(srt_file_array):
        if item.endswith('#'):
            pcnt_file_array_hash.append(pcnt_file_array[idx]+'#')
        else:
            pcnt_file_array_hash.append(pcnt_file_array[idx])

    # assemble the array back to a string
    pcnt_file_cr=' '.join(pcnt_file_array_hash).replace('#','\n')

    return pcnt_file_cr
