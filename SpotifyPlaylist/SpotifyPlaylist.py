#!/usr/bin/env python3.5

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import json

# SPOTIFY_APP_ID = "e1f239ec0ee443689d6786fd3f397af1"
# SPOTIFY_APP_SECRET = "cbecd4d200f8482d910cb1db77d6f10c"

class Playlist():
	def __init__(self, url: str, name="", list_of_tracks=[]):
		self.url = url.replace("\\", "")
		credential_manager = SpotifyClientCredentials(client_id=SPOTIFY_APP_ID, client_secret=SPOTIFY_APP_SECRET)
		self.credentials = spotipy.Spotify(client_credentials_manager=credential_manager)
		if(len(list_of_tracks) == 0): self.track_ids = self.get_track_ids()
		else: self.track_ids = list_of_tracks

	@classmethod
	def from_track_ids(cls, list_of_track_ids: list):
		return cls(url="", list_of_tracks=list_of_track_ids)
	@classmethod
	def from_playlists(cls, name: str, source_one, source_two, token, usr_id):
		manager = PlaylistManager(usr_id, token)
		new_playlist = Playlist.from_track_ids(source_one+source_two)
		if(not manager.is_playlist(name)):
			manager.create_new_playlist(name)
			new_playlist.url = manager.get_playlist_url(name)

		else:
			print("[+] Playlist already exists, not sending API request")
		return new_playlist
	def __add__(self, other):
		return list(set().union(self.get_track_ids(), other.get_track_ids()))	
	def base(self):
		return self.url.split("/")[len(self.url.split("/"))-1]	
	def user_id(self):
		return self.url.split("/")[4]

	def playlist_id(self):
		try:
			return self.base().split("?si=")[0]
		except IndexError:
			return self.base()
	def get_track_ids(self):
		list_of_tracks = self.get_playlist_tracks()
		id_list = []
		for index, element in enumerate(list_of_tracks):
			id_list.append(list_of_tracks[index]['track']['id'])
		return id_list
	def get_playlist_tracks(self):
		results = self.credentials.user_playlist_tracks(self.user_id(), playlist_id="{}".format(self.playlist_id()))
		tracks = results['items']
		while results['next']:
			results = self.manager.elevated_credentials.next(results)
			tracks.extend(results['items'])
		return tracks
	def combine(self, other):
		return list(set().union(self.get_track_ids(), other.get_track_ids()))	
class PlaylistManager():
	def __init__(self, user_id, token):
		self.user_id = user_id
		# credentials that can be used by a regular user and accessing public information
		credential_manager = SpotifyClientCredentials(client_id=SPOTIFY_APP_ID, client_secret=SPOTIFY_APP_SECRET)
		self.credentials = spotipy.Spotify(client_credentials_manager=credential_manager)
		self.elevated_credentials = spotipy.Spotify(auth=token)
		self.token = token
	def create_new_playlist(self, name: str):
		# create new playlist by giving it a name and the user id
		return self.elevated_credentials.user_playlist_create(self.user_id, name)
	def is_playlist(self, playlist_name: str):
		# checks if playlist exists based on name
		# return: boolean
		for index, element in enumerate(self.get_playlists()):
			if(element['name'] == playlist_name):
				return True
		return False
	def get_playlist_id(self, name: str):
		# find the playlist id based on the playlist name
		# return: playlist id 
		for index, element in enumerate(self.get_playlists()):
			if(element['name'] == name):
				return element['id']
		return None
	def get_playlist_url(self, name: str):
		# find the playlist url baed on the playlist name
		# return : Spotify playlist url
		identification_hash = self.get_playlist_id(name)
		for index, element in enumerate(self.get_playlists()):
			if(element['name'] and element['id'] == identification_hash):
				return element['external_urls']['spotify']
		return None
	def get_playlists(self):
		# return a list of json objects representing playlists
		results = self.elevated_credentials.user_playlists(self.user_id)
		playlist_manifest = results['items']
		while results['next']:
			results = self.elevated_credentials.next(results)
			playlist_manifest.extend(results['items'])
		return playlist_manifest
	def search(self, artist: str, track: str):
		result = self.credentials.search(q="artist: {} track: {}".format(artist, track),type='track')
		if(len(result) == 0): return None
		try: return result['tracks']['items'][0]['id']
		except IndexError: return None
	def append_to_playlist(self, playlist: Playlist, track_list: list):
		# add songs to a given Playlist object
		# this does not use the Spotipy API but requests
		url = "https://api.spotify.com/v1/users/{}/playlists/{}/tracks?position=0".format(self.user_id, playlist.playlist_id())
		headers = {
			'Accept': 'application/json', 
			'Content-Type': 'application/json', 
			'Authorization': 'Bearer {}'.format(self.token)
		}
		chunks = [track_list[x:x+100] for x in range(0, len(track_list), 100)]
		for chunk in chunks:
			payload = {
				"position": 0, 
				"uris": ["spotify:track:{}".format(element) for element in chunk] 
			}
			req = requests.post(url, headers=headers, data=json.dumps(payload))
			if req.status_code != 201:
				print('Error: Request returned status code {}. Returned: {}'.format(req.status_code, req.text))

	def truncate_playlist(self, playlist: Playlist):
		# remove the contents of a playlist
		self.elevated_credentials.user_playlist_remove_all_occurrences_of_tracks(self.user_id, playlist.playlist_id(), playlist.track_ids)

