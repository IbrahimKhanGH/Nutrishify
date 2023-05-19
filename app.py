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


def get_top_words(lyrics_list):
    # Combine all the lyrics into a single string
    lyrics_text = " ".join(lyrics_list)

    # Tokenize the string into individual words
    words = re.findall(r'\b\w+\b', lyrics_text)

    # Convert the words to lowercase and remove non-alphanumeric characters
    words = [word.lower() for word in words if word.isalnum()]

    # Filter out stop words
    # Add more stop words as needed
    stop_words = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'his', 'himself', 'she', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
                  'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now']
    words = [word for word in words if word not in stop_words]

    # Count the occurrences of each word
    word_counts = Counter(words)

    # Sort the dictionary based on word frequencies in descending order
    top_words = word_counts.most_common(7)

    # Extract only the words from the top_words list
    top_words_list = [word for word, count in top_words]

    return top_words_list


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

    short_term_lyrics = []
    for song in short_term['items']:
        # Retrieve lyrics for each song and append them to the list
        lyrics = get_lyrics(song['name'], song['artists'][0]['name'])
        short_term_lyrics.append(lyrics)

    # Calculate the top words from the short-term lyrics
    short_term_top_words = get_top_words(short_term_lyrics)

    # Repeat the above steps for medium_term and long_term
    medium_term_lyrics = []
    for song in medium_term['items']:
        lyrics = get_lyrics(song['name'], song['artists'][0]['name'])
        medium_term_lyrics.append(lyrics)

    medium_term_top_words = get_top_words(medium_term_lyrics)

    long_term_lyrics = []
    for song in long_term['items']:
        lyrics = get_lyrics(song['name'], song['artists'][0]['name'])
        long_term_lyrics.append(lyrics)

    long_term_top_words = get_top_words(long_term_lyrics)

    if os.path.exists(".cache"):
        os.remove(".cache")

    return render_template('nutrition.html',
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
