import time
import hashlib
import requests
import json
from dotenv import load_dotenv
import os
import certifi
from pydub import AudioSegment
from moviepy import AudioFileClip

 
 
load_dotenv()
appKey = "17466108920004b7"
secretKey = "affd2b804daf532e0fe01a95474f94df"
 
baseURL = "https://api.speechsuper.com/"
 
timestamp = str(int(time.time()))
 
 
def start_processing(audio_file, reference_text, model="speak.eval.pro"):

    clip = AudioFileClip(audio_file)
    clip.write_audiofile("output.wav")
    print("Success")

    audio = AudioSegment.from_file("output.wav")
    audio = audio.set_frame_rate(16000)
    audio.export("output.wav", format="wav")
    audio_file = "output.wav"
    coreType = model
    refText = reference_text
    audioPath = audio_file
    audioType = "wav"
    audioSampleRate = 16000
    userId = "guest"
 
    url = baseURL + coreType
    connectStr = (appKey + timestamp + secretKey).encode("utf-8")
    connectSig = hashlib.sha1(connectStr).hexdigest()
    startStr = (appKey + timestamp + userId + secretKey).encode("utf-8")
    startSig = hashlib.sha1(startStr).hexdigest()
 
    params = {
        "connect": {
            "cmd": "connect",
            "param": {
                "sdk": {
                    "version": 16777472,
                    "source": 9,
                    "protocol": 2
                },
                "app": {
                    "applicationId": appKey,
                    "sig": connectSig,
                    "timestamp": timestamp
                }
            }
        },
        "start": {
            "cmd": "start",
            "param": {
                "app": {
                    "userId": userId,
                    "applicationId": appKey,
                    "timestamp": timestamp,
                    "sig": startSig
                },
                "audio": {
                    "audioType": audioType,
                    "channel": 1,
                    "sampleBytes": 2,
                    "sampleRate": audioSampleRate
                },
                "request": {
                    "coreType": coreType,
                    "task_type": "ielts_part1",
                    "test_type": "ielts",
                    "question prompt": "Talk about cat",
                    "tokenId": "tokenId",
                    "accent_dialect": "indian",
                    "agegroup": 2
                }
 
            }
        }
    }
    # print("above datas")
    datas = json.dumps(params)
    data = {'text': datas}
    # print("data:",data)
    headers = {"Request-Index": "0"}
    files = {"audio": open(audioPath, 'rb')}
    # res = requests.post(url, data=data, headers=headers, files=files, verify=certifi.where())
    res = requests.post(url, data=data, headers=headers, files=files, verify=False)
    return res.text.encode('utf-8', 'ignore').decode('utf-8')
 
 
if __name__ == '__main__':
  print(start_processing(r"C:\Users\shwethasathish\Downloads\extracted_audio.mp3", "Talk about cat"))
 
 
 
 