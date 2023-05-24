import os
import time
from flask import Flask, render_template, url_for, request, redirect, flash
import string
import random
import eventlet
from flask import Flask, render_template, url_for, request, redirect, flash, session
from flask_login import LoginManager, login_user, current_user, logout_user
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_wtf.csrf import CSRFProtect
from wtform_fields import *
from models import *
from spotifyFunctions import *
import requests
from threading import Thread, Event

secret_key = os.urandom(32)
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET')
app.config['SECRET_KEY'] = secret_key


# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://tlyvqlkvwscyec:eecc49c2e4e8c9479974055ae5a1d14038cf3fb36b17a53187aa149943192aaa@ec2-54-156-53-71.compute-1.amazonaws.com:5432/d6mm9qom3jafo5'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

current_room = ''

# Flask login
login = LoginManager(app)
@@ -26,8 +33,24 @@
# Initialize Flask-SocketIO
socketio = SocketIO(app, manage_session=False)

# Example rooms
ROOMS = ["lounge", "news", "games", "coding"]

thread = Thread()
thread_stop_event = Event()


def GetHostinformation(spotifyOb, room):
    # Retrieve Host information every 1 second and emit to socketio client

    print("hello")
    song = getTrackName(spotifyOb)
    track = getTrackURI(spotifyOb)
    hosttime = getTrackTime(spotifyOb)
    playing = checkPlaying(spotifyOb)
    songName = song

    socketio.emit('some event', {
                  'tracktime': hosttime, 'trackuri': track, 'isplaying': playing}, room=room)
    socketio.sleep(2)


@ login.user_loader
@@ -66,24 +89,90 @@ def login():
    if login_form.validate_on_submit():
        user_object = User.query.filter_by(
            username=login_form.username.data).first()
        login_user(user_object)
        return redirect(url_for('chat'))
        login_user(user_object, remember=True)
        return render_template("createorjoin.html")
        # return redirect(url_for('create-rooms'))

    return render_template("login.html", form=login_form)


@ app.route("/chat", methods=['GET', 'POST'])
def chat():
@ app.route("/create-room", methods=['GET', 'POST'])
def createRoom():
    global current_room

    if not current_user.is_authenticated:
        flash('Please login', 'danger')
        return redirect(url_for('login'))
    if request.method == "POST":
        roomname = request.form["fvideourl"]
        roomID = id_generator()
        current_room = roomname
        session["host"] = True

        # add roomname and ID to database
        room = Roomies(roomname=roomname, roomid=roomID)
        db.session.add(room)
        db.session.commit()
        return redirect(url_for('verify'))

        # Check for room name and ID in database before deploying

    else:
        return render_template('CreateRooms.html')


@app.route("/join-room", methods=['GET', 'POST'])
def joinroom():
    global current_room
    if request.method == "POST":
        roomname = request.form["buttonroom"]
        current_room = roomname.lstrip("Join ")
        session["host"] = False

        return redirect(url_for('verify'))

    else:
        rooms = Roomies.query.all()
        return render_template("joinroom.html", rooms=rooms)


@app.route("/verify")
def verify():
    auth_url = f'{API_BASE}/authorize?client_id={CLI_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}&show_dialog={SHOW_DIALOG}'
    print(auth_url)
    return redirect(auth_url)


@app.route("/api_callback")
def api_callback():

    return render_template('chat.html', username=current_user.username)
    code = request.args.get('code')

    auth_token_url = f"{API_BASE}/api/token"
    res = requests.post(auth_token_url, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://127.0.0.1:5000/api_callback",
        "client_id": CLI_ID,
        "client_secret": CLI_SEC
    })

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')
    res_body = res.json()
    print(res.json())
    session["toke"] = res_body.get("access_token")

    return redirect("spotify-sync")


@ app.route("/spotify-sync", methods=['GET', 'POST'])
def spotifyRoom():
    global current_room
    spotifyOb = spotipy.Spotify(auth=session['toke'])
    songName = "nothing currently synced"
    if session['host'] is True:
        playing = checkPlaying(spotifyOb)
        if playing is True:
            songName = getTrackName(spotifyOb)
            return render_template("spotifyHost.html", currentSong=songName, username=current_user.username, room=current_room, host=session['host'])

    return render_template("spotifyHost.html", currentSong=songName, username=current_user.username, room=current_room, host=session['host'])


@ app.route("/logout", methods=['GET'])
@@ -94,14 +183,63 @@ def logout():
    return redirect(url_for('login'))


@ socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)
@socketio.on('start thread')
def startthread(data):
    global thread
    spotifyOb = spotipy.Spotify(auth=session['toke'])

    if not thread.isAlive():
        print("Starting Thread")
        thread = socketio.start_background_task(
            GetHostinformation(spotifyOb, data['room']))

if __name__ == "__main__":
    socketio.run(app, debug = True)

@socketio.on('join')
def join(data):
    join_room(data['room'])
    send({'msg': data['username'] + " has joined the " +
          data['room'] + "room."}, room=data['room'])


@socketio.on('leave')
def leave(data):
    leave_room(data['room'])
    send({'msg': data['username'] + " has left the " +
          data['room'] + "room."}, room=data['room'])


@socketio.on('my event')
def sync_my_data(data):
    if session['host'] is False:

        spotifyOb = spotipy.Spotify(auth=session['toke'])
        worked = spotifyCheckSync(
            spotifyOb, data['tracktime'], data['trackuri'], data['isplaying'])
        print(worked)


@socketio.on('some event')
def syncuser(data):

    spotifyOb = spotipy.Spotify(auth=session['toke'])
    print(worked)


@socketio.on('message')
def message(data):
    send({'msg': data['msg'], 'username': data['username'],
          'time_stamp': time.strftime('%b-%d %I:%M%p', time.localtime())}, room=data['room'])


# @socketio.on('my event')
# def handle_my_custom_event(json, methods=['GET', 'POST']):
# print('received my event: ' + str(json))
# socketio.emit('my response', json, callback=messageReceived)


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


if __name__ == "__main__":
    socketio.run(app, debug=True)
