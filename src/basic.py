import json
import base64
import os
import sys
import logging
from pathlib import Path
import audioop
from pydub import AudioSegment

from gtts import gTTS
from io import BytesIO
from flask import Flask, render_template
from flask_sockets import Sockets
from geventwebsocket.websocket import WebSocket


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')

HTTP_SERVER_PORT = 6000
LOG_PATH = Path("./call_logs")
HOSTNAME = "dad0.ddns.net"

app = Flask(__name__)
sockets = Sockets(app)


def log_call(start, end, transcript, sid, verdict):
    num = len(os.listdir(LOG_PATH))
    with open(f"call{num}.json") as f:
        json.dump({
            "start": start.isoformat(),
            "duration": (end - start).total_seconds(),
            "SID": sid,
            "verdict": verdict,
            "transcript": transcript,
        }, f)


def log(msg, *args):
    print(f"Media WS: ", msg, *args)


@app.route('/twiml', methods=['POST', 'GET'])
def return_twiml():
    print("POST TwiML")
    return render_template('streams.xml')


@sockets.route('/voice')
def echo(ws: WebSocket):
    log("Connection accepted")
    count = 0
    sid = None

    mp3_fp = BytesIO()
    tts = gTTS("Hi guys, this is a test", lang='en')
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    sound = AudioSegment.from_mp3(mp3_fp)

    sound = sound.set_channels(1)
    sound = sound.set_frame_rate(8000)

    data = sound.raw_data

    ulaw_data = audioop.lin2ulaw(data, 2)

    while not ws.closed:
        message = ws.receive()
        if message is None:
            continue

        data = json.loads(message)
        if data['event'] == "connected":
            log("Connected Message received", message)
        elif data['event'] == "start":
            log("Start Message received", message)
            sid = data['streamSid']
        elif data['event'] == "media":
            if ulaw_data:
                ws.send(json.dumps({
                    "event": "media",
                    "streamSid": sid,
                    "media": {
                        "payload": base64.b64encode(ulaw_data).decode('utf-8')
                    }
                }))
            else:
                pass
                # ws.send(json.dumps({
                #     "event": "media",
                #     "streamSid": sid,
                #     "media": {
                #         "payload": data['media']["payload"]
                #     }
                # }))
        elif data['event'] == 'close':
            pass
        elif data['event'] == "closed":
            break
        else:
            raise RuntimeError(f"Unknown event: {data['event']} | data: {data}")
        count += 1

    log(f"Connection closed | SID: {sid} | messages: {count}")



if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('', HTTP_SERVER_PORT), app, handler_class=WebSocketHandler)
    print("Server listening on: http://localhost:" + str(HTTP_SERVER_PORT))
    server.serve_forever()