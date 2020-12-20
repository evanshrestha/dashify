import sys
import spotipy
import spotipy.util as util
from spotipy import oauth2
from flask import Flask, render_template, session, redirect, request
from flask_session import Session
import os
import uuid

app = Flask(__name__, static_url_path="/static")
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

scope = 'user-library-read playlist-read-private user-read-recently-played'
home_url = 'spotify.evanshrestha.com'
home_url = ''

client_id = os.getenv('DASHIFY_CLIENT_ID')
client_secret = os.getenv('DASHIFY_CLIENT_SECRET')
redirect_uri = os.getenv('DASHIFY_REDIRECT_URI')

cache_folder = './cache/'
if not os.path.exists(cache_folder):
    os.makedirs(cache_folder)

def session_cache_path():
    return cache_folder + session.get('uuid')

def authorize_user():
    if not session.get('uuid'):
        session['uuid'] = str(uuid.uuid4())

    sp_oauth = oauth2.SpotifyOAuth(client_id = client_id, client_secret = client_secret, redirect_uri = redirect_uri, 
        scope=scope, cache_path = session_cache_path())
    
    if request.args.get("code") is not None:
        code = sp_oauth.parse_response_code(request.url)
        token_info = sp_oauth.get_access_token(code)
        session["token"] = token_info['access_token']

    auth_url = sp_oauth.get_authorize_url()
    return auth_url


@app.route('/')
def get_home_page():

    if "token" in session:
        sp = spotipy.Spotify(auth=session["token"])
    else:
        auth = authorize_user()
        return redirect(auth)
    
    playlists = []

    try:
        results = sp.current_user_playlists()
    except spotipy.client.SpotifyException:
        return redirect(auth)

    playlist_items = results['items']

    while results['next']:
        results = sp.next(results)
        playlist_items.extend(results['items'])

    for item in playlist_items:
        playlist_id = item['id']
        playlist_name = item["name"]
        if len(item['images']) > 0:
            playlist_image = item['images'][0]['url']
        else:
            playlist_image = ""
        playlist_owner = item['owner']
        playlist = {
            "id": playlist_id,
            "name": playlist_name,
            "image": playlist_image,
            "owner": playlist_owner
        }
        playlists.append(playlist)
    return render_template("index.html", user=sp.current_user()['display_name'], playlists=playlists, home_url=home_url)

@app.route('/playlist/<playlist_id>')
def get_playlist_info(playlist_id):
    if "token" in session:
        sp = spotipy.Spotify(auth=session["token"])
    else:
        auth = authorize_user()
        return redirect(auth)
    
    songs = []
    results = sp.user_playlist_tracks(sp.current_user()['id'], playlist_id=playlist_id)
    playlist = sp.user_playlist(sp.current_user()['id'], playlist_id=playlist_id)
    tracks = results['items']

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    for item in results['items']:
        track = item['track']
        album = track['album']
        album_images = album['images']
        image_url = ""
        if len(album_images) > 0:
            image_url = album_images[0]['url']

        track_id = track['id']

        song = {"title": track['name'],
                "artist": track['artists'][0]['name'],
                "image": image_url,
                "id": track_id}

        songs.append(song)

    song_ids = [song["id"] for song in songs]
    song_chunks = [song_ids[i*50:i*50 + 50] for i in range((len(songs)+50-1)//50)]
    songs_features = []

    for chunk in song_chunks:
        songs_features.extend(sp.audio_features(chunk))
        
    return render_template("playlist.html", user=sp.current_user()['display_name'], playlist=playlist, songs=songs, songs_features=songs_features, home_url=home_url)

@app.route('/recent')
def get_recent__info():
    if "token" in session:
        sp = spotipy.Spotify(auth=session["token"])
    else:
        auth = authorize_user()
        return redirect(auth)
    
    songs = []

    for item in results['items']:
        track = item['track']
        album = track['album']
        album_images = album['images']
        if len(album_images) > 0:
            image_url = album_images[0]['url']
        else:
            image_url = ""

        track_id = track['id']

        song = {"title": track['name'],
                "artist": track['artists'][0]['name'],
                "image": image_url,
                "id": track_id}

        songs.append(song)

    song_ids = [song["id"] for song in songs]
    song_chunks = [song_ids[i*50:i*50 + 50] for i in range((len(songs)+50-1)//50)]
    songs_features = []

    for chunk in song_chunks:
        songs_features.extend(sp.audio_features(chunk))
        
    return render_template("playlist.html", user=sp.current_user()['display_name'], songs=songs, songs_features=songs_features, home_url=home_url)

@app.route('/track/<track_id>')
def get_track_info(track_id):
    if "token" in session:
        sp = spotipy.Spotify(auth=session["token"])
    else:
        auth = authorize_user()
        return redirect(auth)
    
   
    track = sp.track(track_id)
    print(track)
    return render_template("track.html", track=track, features = get_audio_features(track_id)[0], home_url=home_url)

def get_audio_features(track_id):
    if "token" in session:
        sp = spotipy.Spotify(auth=session["token"])
    else:
        auth = authorize_user()
        return redirect(auth)

    return sp.audio_features(tracks=[track_id])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='9001')
