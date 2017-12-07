from piwho import recognition
import os

path = os.path.dirname(os.path.abspath(__file__))

recog = recognition.SpeakerRecognizer()


try:
    os.remove(path + '/speakers.txt')
except:
    pass

for root, directories, files in os.walk(path):
    for listedfiles in files:
        if "marf" in listedfiles:
            os.remove(os.path.join(root, listedfiles))
            

for root, directories, files in os.walk(path):
    for directory in directories:
        recog.speaker_name = directory
        recog.train_new_data(os.path.join(root, directory))
   

