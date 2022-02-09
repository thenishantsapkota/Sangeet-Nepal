import spotipy
from sangeet_nepal.config import spotify_config
from spotipy.oauth2 import SpotifyClientCredentials


class SpotifyHandler:
    def __init__(self) -> None:
        self.credentials = SpotifyClientCredentials(
            client_id=spotify_config.client_id,
            client_secret=spotify_config.client_secret,
        )
        self.spotify = spotipy.Spotify(client_credentials_manager=self.credentials)

    async def get_tracks_from_playlist(self, playlist_url: str) -> list:
        results = self.spotify.playlist_tracks(playlist_url, additional_types=["track"])

        tracklist = []
        for item in results["items"]:
            if item["track"]["artists"].__len__() == 1:
                tracklist.append(
                    item["track"]["name"] + " - " + item["track"]["artists"][0]["name"]
                )
            else:
                name_string = ""
                for index, b in enumerate(item["track"]["artists"]):
                    name_string += b["name"]
                    if item["track"]["artists"].__len__() - 1 != index:
                        name_string += ", "
                    tracklist.append(item["track"]["name"] + " - " + name_string)

        return tracklist

    async def get_tracks_from_album(self, playlist_url: str) -> list:
        results = self.spotify.album_tracks(playlist_url)
        tracklist = []
        for item in results["items"]:
            if item["artists"].__len__() == 1:
                tracklist.append(item["name"] + " - " + item["artists"][0]["name"])
            else:
                name_string = ""
                for index, b in enumerate(item["artists"]):
                    name_string += b["name"]
                    if item["artists"].__len__() - 1 != index:
                        name_string += ", "
                    tracklist.append(item["name"] + " - " + name_string)

        return tracklist

    async def get_track_from_url(self, track_url: str) -> list:
        result = self.spotify.track(track_url)
        if result["artists"].__len__() == 1:
            return ["{} - {}".format(result["name"], result["artists"][0]["name"])]

        else:
            name_string = ""
            for index, b in enumerate(result["artists"]):
                name_string += b["name"]
                if result["artists"].__len__() - 1 != index:
                    name_string += ", "
            return ["{} - {}".format(result["name"], name_string)]

    async def handle_spotify_url(self, url: str) -> list | None:
        if url.__contains__("playlist"):
            return await self.get_tracks_from_playlist(url)
        elif url.__contains__("album"):
            return await self.get_tracks_from_album(url)
        elif url.__contains__("track"):
            return await self.get_track_from_url(url)
        else:
            return None
