from threading import Thread
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap


# import eventlet
# import asyncio


# eventlet.monkey_patch()

# from gevent import monkey
# monkey.patch_all()


app = Flask(__name__)

socketio = SocketIO(app)
bootstrap = Bootstrap(app)


@app.route('/')
def index():
    return render_template('index.html')



if __name__ == '__main__':
    socketio.run(app, debug=True)
