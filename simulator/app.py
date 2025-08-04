from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from linnstrument import LinnStrument

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def midi_callback(msg):
    socketio.emit('midi_message', msg.dict())

ls = LinnStrument(midi_out_callback=midi_callback)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('touch')
def handle_touch(data):
    col = int(data['col'])
    row = int(data['row'])
    z = int(data['z'])
    touch_id = ls.touch(col, row, z)
    if touch_id is not None:
        emit('touch_id', {'touch_id': touch_id})

@socketio.on('release')
def handle_release(data):
    touch_id = int(data['touch_id'])
    ls.release(touch_id)

if __name__ == '__main__':
    socketio.run(app, debug=True)
