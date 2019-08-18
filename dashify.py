import sys
import spotipy
import spotipy.util as util
from flask import Flask, render_template

app = Flask(__name__, static_url_path="/static")

scope = 'user-library-read playlist-read-private'
username = sys.argv[1]
home_url = sys.argv[2]
token = util.prompt_for_user_token(username, scope)
sp = spotipy.Spotify(auth=token)

@app.route('/')
def get_home_page():
    playlists = []

    results = sp.current_user_playlists()
    playlist_items = results['items']

    while results['next']:
        results = sp.next(results)
        playlist_items.extend(results['items'])

    for item in playlist_items:
        playlist_id = item['id']
        playlist_name = item["name"]
        playlist_image = item['images'][0]['url']
        playlist_owner = item['owner']
        playlist = {
            "id": playlist_id,
            "name": playlist_name,
            "image": playlist_image,
            "owner": playlist_owner
        }
        playlists.append(playlist)
    return render_template("index.html", user=username, playlists=playlists, home_url=home_url)

@app.route('/playlist/<playlist_id>')
def get_playlist_info(playlist_id):
    songs = []
    results = sp.user_playlist_tracks(username, playlist_id=playlist_id)
    tracks = results['items']

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    for item in results['items']:
        track = item['track']
        album = track['album']
        album_images = album['images']
        image_url = album_images[0]['url']

        track_id = track['id']
        print(track['name'] + ' - ' + track['artists'][0]['name'])

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

    return render_template("playlist.html", user=username, songs=songs, songs_features=songs_features, home_url=home_url)

@app.route('/track/<track_id>')
def get_track_info(track_id):
    track = sp.track(track_id)
    print(track)
    return render_template("track.html", track=track, features = get_audio_features(track_id)[0], home_url=home_url)

def get_audio_features(track_id):
    return sp.audio_features(tracks=[track_id])

if __name__ == '__main__':
    app.run(host='0.0.0.0')