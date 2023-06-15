from flask import Flask, render_template, request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)

# Set up the YouTube Data API client
api_key = ''

youtube = build('youtube', 'v3', developerKey=api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    area_of_interest = request.form.get('area_of_interest')
    videos = get_latest_videos(area_of_interest)
    return render_template('result.html', area_of_interest=area_of_interest, videos=videos)


def get_latest_videos(area_of_interest):
    try:
        response = youtube.search().list(
            part='snippet',
            q=area_of_interest,
            order='viewCount',
            maxResults=10
        ).execute()

        videos = []
        for item in response['items']:
            video_id = item['id']['videoId']
            video_title = item['snippet']['title']
            video_thumbnail = item['snippet']['thumbnails']['default']['url']
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            video_likes, video_dislikes = get_video_likes(video_id)
            video_transcript = get_video_transcript(video_id)
            videos.append({
                'title': video_title,
                'thumbnail': video_thumbnail,
                'url': video_url,
                'likes': video_likes,
                'dislikes': video_dislikes,
                'transcript': video_transcript
            })

        return videos
    except HttpError as e:
        print('An error occurred:', e)
        return []

def get_video_likes(video_id):
    try:
        response = youtube.videos().list(
            part='statistics',
            id=video_id
        ).execute()

        video = response['items'][0]
        likes = int(video['statistics']['likeCount'])
        dislikes = int(video['statistics'].get('dislikeCount', 0))
        return likes, dislikes
    except HttpError as e:
        print('An error occurred:', e)
        return None, None

def get_video_transcript(video_id):
    try:
        response = youtube.captions().list(
            part='snippet',
            videoId=video_id
        ).execute()

        captions = response.get('items', [])
        if len(captions) > 0:
            caption_id = captions[0]['id']
            transcript = youtube.captions().download(
                id=caption_id,
                tfmt='srt'
            ).execute()
            transcript_text = process_srt_transcript(transcript)
            return transcript_text
        else:
            return None
    except HttpError as e:
        print('An error occurred:', e)
        return None

def process_srt_transcript(transcript):
    lines = transcript.split('\n')
    text = ''
    for line in lines:
        line = line.strip()
        if line.isdigit() or '-->' in line or line == '':
            continue
        text += line + ' '
    return text

if __name__ == '__main__':
    app.run(debug=True)
