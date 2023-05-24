import os
import json
import spotipy
import spotipy.util as util
from time import sleep
from json.decoder import JSONDecodeError
from spotipy.oauth2 import SpotifyOAuth

# Spotify User Authentication
API_BASE = 'https://accounts.spotify.com'

REDIRECT_URI = "http://127.0.0.1:5000/api_callback"


# Important data for both getTrack and setTrack
SCOPE = 'playlist-read-private, user-read-currently-playing, user-read-playback-state, user-modify-playback-state'

SHOW_DIALOG = True

CLI_ID = 'a9788bb7d269444d8fb92137d71b442e'
# Should never actually go live with this hardcoded in the source code, but for what we're doing it's fine
CLI_SEC = 'b57506a8fb03415a8a66d576184ac0f0'


# spotifySync will use the user id passed into it to get an OAuth token and setup a SpotifyObject
# This function will be a part of both getTrack and setTrack
# It would be best if we could somehow tie this to a user account so that a spotifyAccount wouldn't have to be created everytime


# WORKING
# getTrack will get the track of the current user.
# This should be used to get the data of the host so that others can sync, and to check if the other
#  users are still in sync with the host


def getTrackName(spotifyObject):
    currentTrackJSON = spotifyObject.current_playback()
    type(currentTrackJSON)
    currentTrackData = json.dumps(currentTrackJSON)
    currentTrack = currentTrackJSON['item']['name']
    return currentTrack


# WORKIING
# Gets the unique Track URI
def getTrackURI(spotifyObject):
    currentTrackJSON = spotifyObject.current_playback()
    type(currentTrackJSON)
    currentTrackData = json.dumps(currentTrackJSON)
    currentTrack = currentTrackJSON['item']['uri']
    return currentTrack

# WORKING
# Sets the users track to track that matches the id passed into the function


def setTrack(spotifyObject, trackID):
    # Play a track for a user
    # Testing with 'All Star' with URI spotify:track:3cfOd4CMv2snFaKAnMdnvK
    spotifyObject.add_to_queue(trackID)
    spotifyObject.next_track()

# WORKING
# Pauses the users playback


def pauseTrack(spotifyObject):
    # Pause a user's track
    spotifyObject.pause_playback()

# WORKING (but same as setTrack)
# Plays the users playback


def playTrack(spotifyObject):
    # Play a user's track
    spotifyObject.start_playback()


# Checks if the user is synced with the data passed into it
def spotifyCheckSync(spotifyObject, hostIsPlaying, hostTrackUri, hostTrackTime):

    clientTrackUri = getTrackURI(spotifyObject)
    if (clientTrackUri != hostTrackUri):
        setTrack(spotifyObject, hostTrackUri)
        sleep(0.3)
        if (hostIsPlaying):
            hostTrackTime += 300

    clientTrackTime = getTrackTime(spotifyObject)
    # THIS MARGIN CAN BE EASILY CHANGED, JUST USING 1 SECOND FOR TESTING
    if (abs(int(clientTrackTime) - int(hostTrackTime)) > 5000):
        setTrackTime(spotifyObject, hostTrackTime)

    if hostIsPlaying is True:
        playTrack(spotifyObject)
        return true
        # elif hostIsPlaying is False:
        # pauseTrack(spotifyObject)
    else:
        return ' They are both playing the same song now'

# WORKING
# Gets the ms timestamp at which the users is playing the song


def getTrackTime(spotifyObject):
    currentTrackJSON = spotifyObject.current_playback()
    type(currentTrackJSON)
    currentTrackData = json.dumps(currentTrackJSON)
    currentTrackTime = currentTrackJSON['progress_ms']
    return currentTrackTime


# WORKING
# Set the users track time to the timestamp passed into the fuction
def setTrackTime(spotifyObject, time):
    spotifyObject.seek_track(time)

# WORKING
# Check if the user's playback is playing (true) or paused (false)


def checkPlaying(spotifyObject):
    currentTrackJSON = spotifyObject.current_playback()
    type(currentTrackJSON)
    currentTrackData = json.dumps(currentTrackJSON)
    currentTrackIsPlaying = bool(currentTrackJSON["is_playing"])
    return currentTrackIsPlaying
