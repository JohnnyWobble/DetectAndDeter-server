from gtts import gTTS
# import pyaudio
# import wave
# import librosa
# import soundfile
# import base64
import audioop
from pydub import AudioSegment, playback
from io import BytesIO
from deepspeech import Model
import numpy as np

# mp3_fp = BytesIO()
# tts = gTTS("Hi guys, this is a test", lang='en')
# tts.write_to_fp(mp3_fp)
# mp3_fp.seek(0)

sound = AudioSegment.from_mp3("test4.mp3")


sound = sound.set_channels(1)
# sound = sound.set_frame_rate(8000)
sound1 = sound.set_frame_rate(16000)

data = sound.raw_data
print(data[50000:50100])

ulaw_data = audioop.lin2ulaw(data, 2)

frames = []

# bdata = base64.encodebytes(data)

ds = Model('models/deepspeech-0.9.3-models.pbmm')
ds.enableExternalScorer('models/deepspeech-0.9.3-models.scorer')
print(ds.sampleRate(), ds.beamWidth())
stream = ds.createStream()

print(sound1.get_frame(0))
print(len(sound1.raw_data), len(sound1.get_array_of_samples()))
print(max(sound1.get_array_of_samples()))

arr_sound = np.array(sound1.get_array_of_samples(), dtype=np.int16)

# print(ds.stt(arr_sound))
last = ""
# for n in sound1.get_array_of_samples():
#     stream.feedAudioContent(np.array([n], dtype=np.int16))
#     new = stream.intermediateDecode()
#     if last != new:
#         last = new
#         print(last)
# step = 16000
# for n in range(len(arr_sound)//step):
#     stream.feedAudioContent(arr_sound[n*step:(n+1)*step])
#     print(stream.intermediateDecode())

