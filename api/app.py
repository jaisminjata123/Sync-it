# save this as app.py
import os
import re
import pickle
import flask
from flask import Flask, request, jsonify
from flask_cors import CORS
from googleapiclient.discovery import build
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import google_auth_oauthlib.flow
import google.oauth2.credentials
from google.auth.transport.requests import Request
import sys
import requests
import uuid
import json

app = Flask(__name__)
app.config['credentials'] = None
cors = CORS(app)
app.secret_key = uuid.uuid4().hex
SCOPES = ['https://www.googleapis.com/auth/youtube', 'https://www.googleapis.com/auth/youtube.force-ssl',
          'https://www.googleapis.com/auth/youtubepartner']
CLIENT_SECRETS = ["client_secret.json", "client_secret-1.json", "client_secret-2.json"]
API_KEYS_YOUTUBE = ['AIzaSyAYg6xDI-6WFJTuhjLn4Laon854ul8TVBQ', "AIzaSyAkL3f37KL47XWnh9dR1HdcUGGCddeoAZY",
                    "AIzaSyAH_Hm9kYNFIJIv-iHVBVXqNixJpMBmpBc"]
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['current_file_index'] = 0
app.config['current_username'] = ""
spotify_auth = SpotifyOAuth(client_id="b3fcb55c0ddb41d3953a9244922e46d4",
                            client_secret="ffd69ff41cf94ebda2647276d02f2e38",
                            redirect_uri="https://ytsp.surge.sh/auth/spotify/callback/",
                            scope="user-library-read,playlist-modify-public",
                            cache_path=".cache")


@app.route("/")
def hello():
    return "Hello, World!"


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


def set_credentials(secret_file_name, auth_num, username):
    CLIENT_SECRETS_FILE = secret_file_name
    app.config['current_file_index'] = auth_num
    app.config['current_username'] = username
    credentials = None
    if os.path.exists("token_" + str(auth_num) + "_" + username + ".pickle"):
        print('Loading Credentials From File...')
        with open("token_" + str(auth_num) + "_" + username + ".pickle", 'rb') as token:
            credentials = pickle.load(token)
            app.config['credentials'] = credentials
            return credentials_to_dict(credentials)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print('Refreshing Access Token...')
            credentials.refresh(Request())
            app.config['credentials'] = credentials
            return credentials_to_dict(credentials)
        else:
            print('Fetching New Tokens...')
            flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
            flow.redirect_uri = flask.url_for('google_redirect', _external=True, _scheme='https')
            authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
            flask.session['state'] = state
            flask.session['secret_file'] = CLIENT_SECRETS_FILE
            return flask.redirect(authorization_url)


@app.route('/google_redirect')
def google_redirect():
    # state = flask.session['state']
    # CLIENT_SECRETS_FILE = flask.session['secret_file']
    file_index = app.config["current_file_index"]
    username = app.config['current_username']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS[file_index], scopes=SCOPES)
    flow.redirect_uri = flask.url_for('google_redirect', _external=True, _scheme='https')
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    with open("token_" + str(file_index) + "_" + username + ".pickle", 'wb') as f:
        print('Saving Credentials for Future Use...')
        pickle.dump(credentials, f)
    return flask.redirect("https://ytsp.surge.sh/google/verified?token=" + credentials.token)


@app.route('/api/youtube-login/')
def youtube_login():
    id = request.args.get('id')
    username = request.args.get('username')[:-1]
    return set_credentials(CLIENT_SECRETS[int(id)], int(id), username)


def clean_title(title, artist):
    title = title.lower()
    artist = artist.lower()
    title = title.split('|')[0].strip()
    groups = re.findall(
        '^(.*)(?:\(.*\)).*$',
        title)
    if len(groups) != 0:
        title = groups[0].strip()
    groups = re.findall(
        '^(.*)(?:\[.*\]).*$',
        title)
    if len(groups) != 0:
        title = groups[0].strip()

    if artist != "":
        title = title.replace(artist, "").strip()
    title = title.replace("-", "").strip()
    title = title.split("by")[0].strip()
    title = title.split("sung")[0].strip()
    title = title.split("lyric")[0].strip()
    return title


def clean_owner(video_owner):
    video_owner = video_owner.lower()
    video_owner = video_owner.replace("topic", "").strip()
    video_owner = video_owner.replace("vevo", "").strip()
    return video_owner.replace("-", "").strip()


def create_playlist(title, status, youtube):
    request1 = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": "This is a sample playlist description.",
                "tags": [
                    "sample playlist",
                    "API call"
                ],
                "defaultLanguage": "en"
            },
            "status": {
                "privacyStatus": status
            }
        }
    )
    response = request1.execute()
    return response['id']


def search_youtube(video, next_page_token, youtube):
    request1 = youtube.search().list(
        part="snippet",
        q=video["videoOwner"] + "-" + video["title"],
        pageToken=next_page_token,
        fields="items(id, snippet / title, snippet / channelTitle, id / videoId)"
    )
    return request1.execute()


def search_repeat_youtube(video, next_page_token):
    response = None
    attempts = 0
    response = {"message": "No Quota Available in verified accounts!"}
    while attempts < len(API_KEYS_YOUTUBE):
        try:
            developer_key = API_KEYS_YOUTUBE[attempts]
            youtube = build('youtube', 'v3', developerKey=developer_key)
            response = search_youtube(video, next_page_token, youtube)
            break
        except:
            attempts += 1
            continue
    return response


def insert_video(playlist_id, video_id, count, youtube):
    request1 = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "position": count,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    )
    return request1.execute()


def insert_video_repeat_youtube_auth(new_playlist_id, video_id, count, username):
    attempts = 0
    credentials = []
    while attempts < len(CLIENT_SECRETS):
        credential = get_credentials(attempts, username)
        if credential is not None:
            credentials.append(credential)
        attempts += 1
    if len(credentials) == 0:
        response = {"message": "Authenticate First",  "status": 501}
        return response

    response = {"message": "No Quota Available in verified accounts!", "status": 501}
    for credential in credentials:
        try:
            youtube_authenticated = build('youtube', 'v3', credentials=credential)
            response = insert_video(new_playlist_id, video_id, count, youtube_authenticated)
            break
        except:
            continue
    return response


def playlist_youtube_metadata(playlist_id, youtube):
    request1 = youtube.playlists().list(
        part="snippet,status",
        id=playlist_id,
        fields="items(snippet/title, snippet/description, snippet/channelTitle, status/privacyStatus)"

    )
    return request1.execute()


def playlist_youtube_metadata_repeat(playlist_id):
    response = None
    attempts = 0
    response = {"message": "No Quota Available in verified accounts!"}
    while attempts < len(API_KEYS_YOUTUBE):
        try:
            developer_key = API_KEYS_YOUTUBE[attempts]
            youtube = build('youtube', 'v3', developerKey=developer_key)
            response = playlist_youtube_metadata(playlist_id, youtube)
            break
        except:
            attempts += 1
            continue
    return response


def playlist_youtube_metadata_auth_repeat(new_playlist_id, username):
    attempts = 0
    credentials = []
    while attempts < len(CLIENT_SECRETS):
        credential = get_credentials(attempts, username)
        if credential is not None:
            credentials.append(credential)
        attempts += 1
    if len(credentials) == 0:
        response = {"message": "Authenticate First", "status": 501}
        return response

    response = {"message": "No Quota Available in verified accounts!", "status": 502}
    for credential in credentials:
        try:
            youtube_authenticated = build('youtube', 'v3', credentials=credential)
            response = playlist_youtube_metadata(new_playlist_id, youtube_authenticated)
            break
        except:
            continue
    return response


def get_playlist_item_youtube(playlist_id, next_page_token, youtube):
    request1 = youtube.playlistItems().list(
        part='contentDetails,id,snippet,status',
        playlistId=playlist_id,
        pageToken=next_page_token,
        maxResults=50
    )
    return request1.execute()


def get_playlist_item_repeat_youtube(playlist_id, next_page_token):
    response = None
    attempts = 0
    response = {"message": "No Quota Available in verified accounts!"}
    while attempts < len(API_KEYS_YOUTUBE):
        try:
            developer_key = API_KEYS_YOUTUBE[attempts]
            youtube = build('youtube', 'v3', developerKey=developer_key)
            response = get_playlist_item_youtube(playlist_id, next_page_token, youtube)
            break
        except:
            attempts += 1
            continue
    return response


def get_credentials(attempts, username):
    if os.path.exists("token_" + str(attempts) + "_" + username + ".pickle"):
        print('Loading Credentials From File...')
        with open("token_" + str(attempts) + "_" + username + ".pickle", 'rb') as token:
            credentials = pickle.load(token)
            app.config['credentials'] = credentials
            return credentials


def get_playlist_item_repeat_youtube_auth(playlist_id, next_page_token, username):
    attempts = 0
    credentials = []
    while attempts < len(CLIENT_SECRETS):
        credential = get_credentials(attempts, username)
        if credential is not None:
            credentials.append(credential)
        attempts += 1
    if len(credentials) == 0:
        response = {"message": "Authenticate First", "status": 501}
        return response

    response = {"message": "No Quota Available in verified accounts!", "status": 502}
    for credential in credentials:
        try:
            youtube_authenticated = build('youtube', 'v3', credentials=credential)
            response = get_playlist_item_youtube(playlist_id, next_page_token, youtube_authenticated)
            break
        except:
            continue
    return response


def create_playlist_repeat_youtube_auth(new_playlist_title, status, username):
    attempts = 0
    credentials = []
    while attempts < len(CLIENT_SECRETS):
        credential = get_credentials(attempts, username)
        if credential is not None:
            credentials.append(credential)
        attempts += 1
    if len(credentials) == 0:
        response = {"message": "Authenticate First", "status": 501}
        return response

    response = {"message": "No Quota Available in verified accounts!", "status": 501}
    for credential in credentials:
        try:
            youtube_authenticated = build('youtube', 'v3', credentials=credential)
            response = create_playlist(new_playlist_title, status, youtube_authenticated)
            break
        except:
            continue
    return response


@app.route('/api/spotify-login')
def get_auth_token_spotify():
    auth_url = spotify_auth.get_authorize_url()
    return jsonify(auth_url=auth_url)


@app.route('/api/spotify/get-token')
def get_access_token():
    code = request.args.get('code')
    try:
        auth_token = spotify_auth.get_access_token(code)
        if os.path.exists(".cache"):
            os.remove(".cache")
        if spotify_auth.is_token_expired(auth_token):
            if os.path.exists(".cache"):
                os.remove(".cache")
            return jsonify(auth_token=spotify_auth.refresh_access_token(auth_token["refresh_token"]))
        if os.path.exists(".cache"):
            os.remove(".cache")
        return jsonify(auth_token=auth_token)
    except:
        return jsonify(auth_token="")


@app.route('/api/sp-yt/playlist', methods=["POST"])
def sp_to_yt_playlist_controller():
    videos_list = []
    sp_yt_mapping = []
    unmapped = []
    new_playlist_title = ""
    yt_playlist_id = ""
    if request.method == 'POST' and request.data:
        playlist_id = request.json['playlistId']
        if "playlist_name" in request.json:
            new_playlist_title = request.json['playlist_name']
        if "target_playlist_id" in request.json:
            yt_playlist_id = request.json['target_playlist_id']

        auth_token = request.json['auth_token']
        username = request.json['username']
        sp = spotipy.Spotify(auth=auth_token)
        limit = 50
        offset = 0
        total = 1000
        while offset < total:
            tracks = sp.playlist_items(playlist_id, limit=limit, offset=offset)
            total = tracks['total']
            if len(tracks['items']) == 0:
                break
            offset += limit
            for track in tracks['items']:
                video_owner = clean_owner(track['track']['artists'][0]['name'])
                video_info = {'videoId': track['track']['uri'],
                              'title': clean_title(track['track']['name'], video_owner),
                              "videoOwner": video_owner}
                videos_list.append(video_info)

        for video in videos_list:
            next_page_token = ""
            end_of_call = False
            hard_max = 100
            current = 0
            matched = False
            while not end_of_call and current < hard_max:
                response = search_repeat_youtube(video, next_page_token)
                if response is None:
                    return jsonify(videos_list=videos_list)
                if len(response['items']) == 0:
                    break
                current += len(response['items'])
                if 'nextPageToken' not in response:
                    end_of_call = True
                else:
                    next_page_token = response['nextPageToken']
                for yt_video in response['items']:
                    if video['title'] in yt_video['snippet']['title'].lower() or video['videoOwner'] in \
                            yt_video['snippet'][
                                'channelTitle'].lower():
                        best_match = {'sp_uri': video["videoId"], 'artist': video["videoOwner"],
                                      'yt_video_id': yt_video['id']['videoId'],
                                      'yt_video_owner': yt_video['snippet']['channelTitle'],
                                      'title': yt_video['snippet']['title']}
                        matched = True
                        print(best_match)
                        sp_yt_mapping.append(best_match)
                        end_of_call = True
                        break
            if not matched:
                unmapped.append(video)

        if yt_playlist_id == "":
            yt_playlist_id = create_playlist_repeat_youtube_auth(new_playlist_title, "private", username)
        count = 0
        for video_mapping in sp_yt_mapping:
            insert_video_repeat_youtube_auth(yt_playlist_id, video_mapping['yt_video_id'], count, username)
            count += 1

    response = {"mapped_list": sp_yt_mapping, "unmapped_list": unmapped, "link": yt_playlist_id}
    return jsonify(data=response)


def compress_metadata_response(response):
    info = {"channel_title": response["items"][0]["snippet"]["channelTitle"],
            "description": response["items"][0]["snippet"]["description"],
            "title": response["items"][0]["snippet"]["title"],
            "status": response["items"][0]["status"]["privacyStatus"]}
    return info


@app.route('/api/spotify-playlist-metadata', methods=["POST"])
def sp_playlist_metadata():
    response = []
    if request.method == 'POST' and request.data:
        playlist_id = request.json['playlistId']
        auth_token = request.json['auth_token']
        sp = spotipy.Spotify(auth=auth_token)
        response = sp.playlist(playlist_id, fields="collaborative,description,name,owner.display_name,public")
    return jsonify(metadata=response)


@app.route('/api/youtube-playlist-metadata', methods=['POST'])
def yt_playlist_metadata():
    if request.method == 'POST' and request.data:
        playlist_id = request.json['playlistId']
        username = request.json['username']
        response = playlist_youtube_metadata_repeat(playlist_id)
        if len(response['items']) == 0:
            response = playlist_youtube_metadata_auth_repeat(playlist_id, username)
            if "message" in response:
                return json.dumps(response), response['status']
            if len(response['items']) == 0:
                return jsonify(metadata=[])
            return jsonify(metadata=compress_metadata_response(response))
        else:
            return jsonify(metadata=compress_metadata_response(response))
    return jsonify(metadata=[])


@app.route('/api/yt-sp/playlist', methods=["POST"])
def yt_to_sp_playlist_controller():
    videos_list = []
    yt_sp_mapping = []
    unmapped = []
    new_playlist_name = ""
    sp_playlist_id = ""
    if request.method == 'POST' and request.data:
        playlist_id = request.json['playlistId']
        if "playlist_name" in request.json:
            new_playlist_name = request.json['playlist_name']
        if "target_playlist_id" in request.json:
            sp_playlist_id = request.json['target_playlist_id']
        auth_token = request.json['auth_token']
        status = request.json['status']
        username = request.json['username']
        sp = spotipy.Spotify(auth=auth_token)
        next_page_token = ""
        end_of_call = False
        while not end_of_call:
            response = None
            if status != "private":
                response = get_playlist_item_repeat_youtube(playlist_id, next_page_token)
            else:
                response = get_playlist_item_repeat_youtube_auth(playlist_id, next_page_token, username)

            if response is None:
                response = {"message": "something went wrong!"}
            if "message" in response:
                return json.dumps(response), response['status']
            if 'nextPageToken' not in response:
                end_of_call = True
            else:
                next_page_token = response['nextPageToken']
            for item in response['items']:
                video_info = {'videoId': item['contentDetails']['videoId'], 'title': item['snippet']['title'],
                              "videoOwner": item['snippet']['videoOwnerChannelTitle']}
                videos_list.append(video_info)

        for video in videos_list:
            limit = 50
            offset = 0
            hard_max = 500
            video['videoOwner'] = clean_owner(video['videoOwner'])
            best_artist = {'uri': "", 'name': "", "followers": 5000}
            while offset < hard_max:
                spotify_artists = sp.search(q=video['videoOwner'], type='artist', offset=offset, limit=limit)
                artists = spotify_artists['artists']
                if len(artists['items']) == 0:
                    break
                offset += limit
                for artist in artists['items']:
                    if artist['followers']['total'] > best_artist['followers'] and artist['name'].lower() in video[
                        'videoOwner']:
                        best_artist['uri'] = artist['uri']
                        best_artist['name'] = artist['name']
                        best_artist['followers'] = artist['followers']['total']

            best_match = {'uri': "", 'artist': "", 'popularity': 0, 'yt_video_id': video['videoId'],
                          'yt_video_owner': video['videoOwner'], 'title':""}
            print(best_artist)
            video['title'] = clean_title(video['title'], best_artist['name'])
            if video['title'] == "":
                continue
            offset = 0
            while offset < hard_max:
                q = ""
                if best_artist['name'] == "":
                    q = video['title']
                else:
                    q = best_artist['name'] + " " + video['title']
                spotify_tracks = sp.search(q=q, type='track', offset=offset, limit=limit)
                tracks = spotify_tracks['tracks']
                if len(tracks['items']) == 0:
                    break
                offset += limit
                for track in tracks['items']:
                    if track['popularity'] > best_match['popularity']:
                        best_match['uri'] = track['uri']
                        best_match['artist'] = track['artists'][0]['name']
                        best_match['popularity'] = track['popularity']
                        best_match['title'] = track['name']
            print(best_match)
            if best_match['uri'] != '':
                yt_sp_mapping.append(best_match)
            else:
                unmapped.append(video)
        user_id = sp.me()['id']
        if sp_playlist_id == "":
            created_playlist_response = sp.user_playlist_create(user_id, new_playlist_name)
            sp_playlist_id = created_playlist_response['id']
        uris_list = [matched['uri'] for matched in yt_sp_mapping]
        for i in range(0, len(uris_list), 100):
            sp.playlist_add_items(sp_playlist_id, uris_list[i:i + 100])
        for video in unmapped:
            print(video)
    response = {"mapped_list": yt_sp_mapping, "unmapped_list": unmapped, "link": sp_playlist_id}
    return jsonify(data=response)


if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True, port=3000)
