from flask import Flask, request, url_for, session, redirect, render_template
import lyricsgenius
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
import re
import time
from time import gmtime, strftime
from credentials import CLIENT_ID, CLIENT_SECRET, GENIUS_KEY, SECRET_KEY
import os
import concurrent.futures
from flask import jsonify
from stop_words import stop_words_list

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
app.config['SESSION_COOKIE_NAME'] = 'Nutrishify Cookie'

genius = lyricsgenius.Genius(GENIUS_KEY)





@app.route('/')
@app.route('/home')
def home():
    name = 'username'
    return render_template('home.html', title='Welcome', username=name)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

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
    return redirect(url_for("chooseLabel", _external=True))


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

@app.route('/chooseLabel')
def chooseLabel():
    return render_template('chooseLabel.html')
    
@app.route('/artistLabel')
def artistLabel():
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(
        auth=token_info['access_token'],
    )

    current_user_name = sp.current_user()['display_name']

    short_term = sp.current_user_top_artists(
        limit=7,
        offset=0,
        time_range=SHORT_TERM,
    )
    medium_term = sp.current_user_top_artists(
        limit=7,
        offset=0,
        time_range=MEDIUM_TERM,
    )
    long_term = sp.current_user_top_artists(
        limit=7,
        offset=0,
        time_range=LONG_TERM,
    )

    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    market = request.args.get('market', default=None, type=str)

    tracks = []
    total = limit  # Initial value to enter the loop


    return render_template('Artist.html', user_display_name=current_user_name,
                           short_term=short_term, medium_term=medium_term,
                           long_term=long_term, #artist_percentages=artist_percentages, 
                           limit=limit)


@app.route('/songLabel')
def songLabel():
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
        limit=10,
        offset=0,
        time_range=SHORT_TERM,
    )
    medium_term = sp.current_user_top_tracks(
        limit=20,
        offset=0,
        time_range=MEDIUM_TERM,
    )
    long_term = sp.current_user_top_tracks(
        limit=30,
        offset=0,
        time_range=LONG_TERM,
    )
    
    return render_template('Song.html',user_display_name=current_user_name, short_term=short_term, medium_term=medium_term, long_term=long_term)

    


@app.template_filter('word_count')
def word_count_filter(s):
    if isinstance(s, list):
        # If it's a list, join the elements into a string
        s = ' '.join(s)
    return len(s.split())

def get_top_words(lyrics_list):
    # Combine all the lyrics into a single string
    lyrics_text = " ".join(lyrics_list)

    # Tokenize the string into individual words
    words = re.findall(r'\b\w+\b', lyrics_text)

    # Convert the words to lowercase and remove non-alphanumeric characters
    words = [word.lower() for word in words if word.isalnum()]

    # Filter out stop words
    # Add more stop words as needed
    stop_words = stop_words_list
    words = [word for word in words if word not in stop_words]

    words = [word for word in words if len(word) <= 15]

    # Count the occurrences of each word
    word_counts = Counter(words)

    # Calculate the total number of lyrics
    total_lyrics = len(lyrics_list)

    # Calculate the percentage of occurrences for each word
    top_words_list = []
    for word, count in word_counts.most_common(7):
        top_words_list.append((word[:25].capitalize(), count))

    return top_words_list 


@app.route('/wordLabel')
def wordLabel():
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
        limit=15,
        offset=0,
        time_range=SHORT_TERM,
    )
    medium_term = sp.current_user_top_tracks(
        limit=30,
        offset=0,
        time_range=MEDIUM_TERM,
    )
    long_term = sp.current_user_top_tracks(
        limit=45,
        offset=0,
        time_range=LONG_TERM,
    )

    def clean_lyrics(lyrics):
        # Remove contributors' names
        cleaned_lyrics = re.sub(r'\[\w+\]', '', lyrics)

        # Remove line breaks
        cleaned_lyrics = cleaned_lyrics.replace('\n', ' ')

        # Remove numbers and special characters
        cleaned_lyrics = re.sub(r'[^a-zA-Z\s]', '', cleaned_lyrics)

        # Replace consecutive whitespace characters with a single space
        cleaned_lyrics = re.sub(r'\s+', ' ', cleaned_lyrics)

        # Convert lyrics to lowercase
        cleaned_lyrics = cleaned_lyrics.lower()

        return cleaned_lyrics

    def get_lyrics(song_name, artist_name):
        # Format the song name and artist name for the search query
        search_query = f'{song_name} {artist_name}'

        # Search for the song lyrics
        song = genius.search_song(search_query)

        if song is not None and artist_name.lower() in song.artist.lower():
            lyrics = clean_lyrics(song.lyrics)  # Clean the lyrics
            return lyrics
        else:
            # If the song wasn't found, try removing the featuring artist information and search again
            if "(feat." in song_name:
                modified_song_name = song_name[:song_name.index(
                    "(feat.")].strip()
                search_query = f'{modified_song_name} {artist_name}'
                song = genius.search_song(search_query)

                if song is not None and artist_name.lower() in song.artist.lower():
                    lyrics = clean_lyrics(song.lyrics)  # Clean the lyrics
                return lyrics

            # If the song still wasn't found, try swapping the position of the song name and artist name in the search query
            search_query_swapped = f'{artist_name} {song_name}'
            song = genius.search_song(search_query_swapped)

            if song is not None and artist_name.lower() in song.artist.lower():
                lyrics = clean_lyrics(song.lyrics)  # Clean the lyrics
                return lyrics

            # If the song still wasn't found, return 'None'
            return 'None'
            

    # Define a function to fetch lyrics
    def fetch_lyrics(song):
        song_name = song['name']
        artist_name = song['artists'][0]['name']
        return get_lyrics(song_name, artist_name)

    # Collect song names and artist names for all the short-term tracks
    short_term_song_names = [song['name'] for song in short_term['items']]
    short_term_artist_names = [song['artists'][0]['name'] for song in short_term['items']]

    # Use concurrent.futures to fetch lyrics in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        short_term_lyrics = list(executor.map(fetch_lyrics, short_term['items']))

    # Calculate the top from the short-term lyrics
    short_term_top_words = get_top_words(short_term_lyrics)

    # Repeat the above steps for medium_term and long_term
    medium_term_song_names = [song['name'] for song in medium_term['items']]
    medium_term_artist_names = [song['artists'][0]['name'] for song in medium_term['items']]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        medium_term_lyrics = list(executor.map(fetch_lyrics, medium_term['items']))

    medium_term_top_words = get_top_words(medium_term_lyrics)

    long_term_song_names = [song['name'] for song in long_term['items']]
    long_term_artist_names = [song['artists'][0]['name'] for song in long_term['items']]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        long_term_lyrics = list(executor.map(fetch_lyrics, long_term['items']))

    long_term_top_words = get_top_words(long_term_lyrics)


    if os.path.exists(".cache"):
        os.remove(".cache")

    return render_template('Word.html',
                           user_display_name=current_user_name,
                           short_term=short_term,
                           medium_term=medium_term,
                           long_term=long_term,
                           short_term_lyrics=short_term_lyrics,
                           medium_term_lyrics=medium_term_lyrics,
                           long_term_lyrics=long_term_lyrics,
                           short_term_top_words=short_term_top_words,
                           medium_term_top_words=medium_term_top_words,
                           long_term_top_words=long_term_top_words, 
                           currentTime=gmtime())

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

