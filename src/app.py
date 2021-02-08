import json
import base64
import sys
import logging
from pathlib import Path

from flask import Flask, render_template
from flask_sockets import Sockets
from geventwebsocket.websocket import WebSocket

from detectanddeter import DetectAndDeter

logging.basicConfig(filename='detectanddeter.log', level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
# logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
# logging.getLogger("websocket").setLevel(logging.WARNING)

logging.info(" --- STARTING ---")
HOSTNAME = "dad0.ddns.net"
HTTP_SERVER_PORT = 6000
LOG_PATH = Path("./call_logs")

app = Flask(__name__)
app.config['DEBUG'] = False
# app.config['SECRET_KEY'] = 'secret!'
sockets = Sockets(app)


@app.route('/twiml', methods=['POST', 'GET'])
def return_twiml():
    print("POST TwiML")
    return render_template('streams.xml')


@sockets.route('/voice')
def echo(ws: WebSocket):
    print("Connection accepted")
    count = 0
    sid = None
    dad = DetectAndDeter()
    in_queue, out_queue = dad.queues
    dad.start()

    while not ws.closed:
        message = ws.receive()
        if message is None:
            continue

        data = json.loads(message)
        if data['event'] == "connected":
            pass
        elif data['event'] == "start":
            sid = data['streamSid']
        elif data['event'] == "media":
            in_queue.put(base64.b64decode(data['media']['payload']))
            if not out_queue.empty():
                ws.send(json.dumps({
                    "event": "media",
                    "streamSid": sid,
                    "media": {
                        "payload": out_queue.get()
                    }}))
        elif data['event'] == 'stop':
            pass
        elif data['event'] == "closed":
            break
        else:
            raise RuntimeError(f"Unknown event: {data['event']} | data: {data}")
        count += 1

    dad.close()
    logging.info(f"Connection closed | SID: {sid} | messages: {count}")


if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('', HTTP_SERVER_PORT), app, handler_class=WebSocketHandler)
    print("Server listening on: http://localhost:" + str(HTTP_SERVER_PORT))
    server.serve_forever()
