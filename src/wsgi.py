from app import socketio, app
import logging

if __name__ == '__main__':
    # logging.debug("STARTING")
    socketio.run(app, debug=True)
