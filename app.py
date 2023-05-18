from flask import Flask, request, url_for, session, redirect, render_template
import lyricsgenius
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from time import gmtime, strftime
from credentials import CLIENT_ID, CLIENT_SECRET, GENIUS_KEY, SECRET_KEY
import os


if __name__ == '__main__':
    app.run()

# Defining consts
TOKEN_CODE = "token_info"
MEDIUM_TERM = "medium_term"
SHORT_TERM = "short_term"
LONG_TERM = "long_term"


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri="http://127.0.0.1:5000/redirect",
        scope="user-top-read user-library-read"
    )


app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_NAME'] = 'Eriks Cookie'

genius = lyricsgenius.Genius(GENIUS_KEY)


@app.route('/')
def index():
    name = 'username'
    return render_template('index.html', title='Welcome', username=name)


@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_CODE] = token_info
    return redirect(url_for("getTracks", _external=True))


def get_token():
    token_info = session.get(TOKEN_CODE, None)
    if not token_info:
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info


@app.route('/getTracks')
def getTracks():
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(
        auth=token_info['access_token'],
    )

    current_user_name = sp.current_user()['display_name']
    short_term = sp.current_user_top_tracks(
        limit=5,
        offset=0,
        time_range=SHORT_TERM,
    )
    medium_term = sp.current_user_top_tracks(
        limit=5,
        offset=0,
        time_range=MEDIUM_TERM,
    )
    long_term = sp.current_user_top_tracks(
        limit=5,
        offset=0,
        time_range=LONG_TERM,
    )

    genius = lyricsgenius.Genius(GENIUS_KEY)
    song_name = short_term['items'][0]['name']
    artist_name = short_term['items'][0]['artists'][0]['name']
    song = genius.search_song(song_name, artist_name)

    def get_lyrics(song_name, artist_name):
        # Format the song name and artist name for the search query
        search_query = f'{song_name} {artist_name}'
        
        # Search for the song lyrics
        song = genius.search_song(search_query)
        
        if song is not None:
            return song.lyrics
        else:
            return 'Lyrics not found'


    short_term_lyrics = []
    for song in short_term['items']:
        # Retrieve lyrics for each song and append them to the list
        lyrics = get_lyrics(song['name'], song['artists'][0]['name'])
        short_term_lyrics.append(lyrics)

    # Repeat the above steps for medium_term and long_term
    medium_term_lyrics = []
    for song in medium_term['items']:
        lyrics = get_lyrics(song['name'], song['artists'][0]['name'])
        medium_term_lyrics.append(lyrics)

    long_term_lyrics = []
    for song in long_term['items']:
        lyrics = get_lyrics(song['name'], song['artists'][0]['name'])
        long_term_lyrics.append(lyrics)

    if os.path.exists(".cache"):
        os.remove(".cache")

    return render_template('nutrition.html', user_display_name=current_user_name, short_term=short_term, medium_term=medium_term, long_term=long_term, short_term_lyrics=short_term_lyrics, medium_term_lyrics=medium_term_lyrics, long_term_lyrics=long_term_lyrics, currentTime=gmtime())



@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    return strftime("%a, %d %b %Y", date)


@app.template_filter('mmss')
def _jinja2_filter_miliseconds(time, fmt=None):
    time = int(time / 1000)
    minutes = time // 60
    seconds = time % 60
    if seconds < 10:
        return str(minutes) + ":0" + str(seconds)
    return str(minutes) + ":" + str(seconds)
