from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run

def toValidFilename(value):
    valid_chars = "-_.()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join([c for c in value if c in valid_chars])
 
CLIENT_SECRETS_FILE = "client_secrets.json"
OAUTH_TOKEN_FILE = "oauth2.json"
SCOPE = "https://www.googleapis.com/auth/youtube"
 
flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                               message="Missing client_secrets.json",
                               scope=SCOPE)
storage = Storage(OAUTH_TOKEN_FILE)
credentials = storage.get()
 
if credentials is None or credentials.invalid:
    print('No credentials, running authentication flow to get OAuth token')
    credentials = run(flow, storage)

from apiclient.discovery import build
from httplib2 import Http
 
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
 
def buildAPI():
    http = Http()
    http = credentials.authorize(http)
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http=http)
 
if credentials is None or credentials.invalid:
    print('No credentials, running authentication flow to get OAuth token')
    credentials = run(flow, storage)
else:
    youtube = buildAPI()
    channels = youtube.channels().list(part='contentDetails', mine=True).execute()
    watchLaterID = channels['items'][0]['contentDetails']['relatedPlaylists']['watchLater']
    videos = youtube.playlistItems().list(
        part='snippet',
        playlistId=watchLaterID, maxResults=50
    ).execute()['items']
    print('Videos to download: %s' % len(videos))

from subprocess import call
 
STORAGE_PATH = "storage/"
 
for video in videos:
    video_id = video["snippet"]["resourceId"]["videoId"]
    video_title = video["snippet"]["title"]
    video_filename = '%s%s %s.%%(ext)s' % (STORAGE_PATH, toValidFilename(video_title), video_id)
    print video_id
    print video_title
    print video_filename
    try:
        if call('youtube-dl -o "%s" http://www.youtube.com/watch?v=%s' % (video_filename, video_id), shell=True):
            # Non-valid return code
            print 'Invalid return code. Stopping.'
            break
    except Exception as e:
        # Download can resume, so don't delete the file
        print('%s' % e)
        break
    youtube = buildAPI()
    youtube.playlistItems().delete(id=video["id"]).execute()
