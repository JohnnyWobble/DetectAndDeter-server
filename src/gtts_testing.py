from gtts import gTTS
import pyaudio
import wave
import librosa
import soundfile
import base64
import audioop
from pydub import AudioSegment, playback
from io import BytesIO

mp3_fp = BytesIO()
tts = gTTS("Hi guys, this is is a test", lang='en')
tts.write_to_fp(mp3_fp)
mp3_fp.seek(0)

sound = AudioSegment.from_mp3(mp3_fp)

sound = sound.set_channels(1)
sound = sound.set_frame_rate(8000)

print(len(sound))

data = sound.raw_data

ulaw_data = audioop.lin2ulaw(data, 2)

# print(len(data), type(data), len(data)/96)
print(len(ulaw_data), type(ulaw_data), len(ulaw_data)/384)
frames = []

bdata = base64.encodebytes(data)
# print(len(bdata), bdata)
# b = bdata[:1000]
# bd = base64.decodebytes(b)
# print("_---------------------")
# print(bd)
# bytearray.

# sound, rate = librosa.load("tmp.mp3")
# print(fp)
# audio = pyaudio.PyAudio()