import os
import re
import spotipy
from spotipy.client import Spotify
from spotipy.oauth2 import SpotifyOAuth
import configparser
import requests
from bs4 import BeautifulSoup

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config', 'credentials.cfg'))

spotify_cred_dict = {}
spotify_cred_dict['spotify_username'] = config.get('spotify', 'spotify_username')
spotify_cred_dict['spotify_client_id'] = config.get('spotify', 'spotify_client_id')
spotify_cred_dict['spotify_client_secret'] = config.get('spotify', 'spotify_client_secret')
spotify_cred_dict['spotify_redirect_uri'] = config.get('spotify', 'spotify_redirect_uri')

genius_cred_dict = {}
genius_cred_dict['genius_access_token'] = config.get('genius', 'genius_client_access_token')

spotify_scope = 'user-read-currently-playing'


class SpotifyLyrics:

    def create_spotify_client(self, token_param_dict, scope):
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=token_param_dict['spotify_client_id'],
                client_secret=token_param_dict['spotify_client_secret'],
                redirect_uri=token_param_dict['spotify_redirect_uri'],
                scope=scope
            )
        )

    def get_current_song_with_progression(self, spotify_client: Spotify):
        current_song = spotify_client.currently_playing()
        song_progression = (current_song['item']['duration_ms'] -
                            current_song['progress_ms']) / 1000
        artist = current_song['item']['artists'][0]['name']
        song = current_song['item']['name']
        print("You're currently listening to:")
        print('\nSong: {}\nArtist: {}'.format(song, artist))
        print('Remaining Time: {} seconds'.format(song_progression))
        return artist, song, song_progression

    def get_song_info(self, song_name, artist_name):
        base_url = 'https://api.genius.com'
        headers = {'Authorization': 'Bearer ' + genius_cred_dict['genius_access_token']}
        search_url = base_url + '/search'
        data = {'q': song_name + ' ' + artist_name}
        genius_song_info_response = requests.get(search_url, data=data, headers=headers).json()
        song_info = None
        for hit in genius_song_info_response['response']['hits']:
            if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
                song_info = hit
                break
        return song_info

    def get_genius_song_url(self, song_info):
        return song_info['result']['url']

    def scrape_lyrics_from_genius_song_url_response(self, genius_song_url):
        headers = {'Authorization': 'Bearer ' + genius_cred_dict['genius_access_token']}
        genius_song_lyrics_response = requests.get(genius_song_url, headers=headers)
        if genius_song_lyrics_response.status_code == 200:
            html = BeautifulSoup(genius_song_lyrics_response.text.replace(
                '<br/>', '\n'), features="html.parser")
            # Extract lyrics from beautifulsoup response using the correct prefix {"class": "lyrics"}

            # Determine the class of the div
            div = html.find("div", class_=re.compile("^lyrics$|Lyrics__Root"))
            if div is None:
                print("Couldn't find the lyrics section. ")
                return None

            lyrics = div.get_text()
            # Remove [Verse], [Bridge], etc.
            lyrics = re.sub(r'(\[.*?\])*', '', lyrics)
            lyrics = re.sub('\n{2}', '\n', lyrics)  # Gaps between verses
            print(lyrics.strip("\n"))


if __name__ == "__main__":
    spotify_lyrics = SpotifyLyrics()
    spotify_client = spotify_lyrics.create_spotify_client(spotify_cred_dict, spotify_scope)
    artist, song, progression = spotify_lyrics.get_current_song_with_progression(spotify_client)
    song_info = spotify_lyrics.get_song_info(artist_name=artist, song_name=song)
    genius_song_url = spotify_lyrics.get_genius_song_url(song_info)
    spotify_lyrics.scrape_lyrics_from_genius_song_url_response(genius_song_url)
