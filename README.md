# hotword

Hotword detector for Snips
https://github.com/snipsco/snips-platform-documentation

uses snowboy https://github.com/Kitt-AI/snowboy 
- you can build your own hotword or use one from the many already created https://snowboy.kitt.ai (login to access)
- install and built it yourself
- or get pre-compiled binaries from https://github.com/Kitt-AI/snowboy#precompiled-binaries-with-python-demo
- place the pmdl file with the hotword.py file (this is the hotword model file)


Piwho https://github.com/Adirockzz95/Piwho
- used for "speaker identification".. who said the hotword
- you train up users (min of 2 needed to work)
- the two trained files created by the train.py file need to be with the pmdl and hotword.py files
- requires "pip install watchdog"

Pytoml pip install pytoml
- used to read the snips.toml file for properties

paho mqtt client pip install paho-mqtt
- MQTT !!!
- In hotword.py change the MQTT info to your address and port if its not set in the toml file


# my snips setup
I use the Snips as Client/Server 

the clients have only Snips-Audio-Server installed and running Each client has either a Respeaker 4mic or 2mic HAT for listening mics and LEDs these also have custom code listening on mqtt for ques on when to turn their LED's on/off

the server does the hard work it has Snips-Audio-Server, Snips-ASR, Snips-Dialogue, Snips-Queries -The server uses the custom hotword code here on github -It listens for the hotword "hey janet" to activate -When it hears "hey janet" it also does a speaker identification using the altered piwho code included.. I altered the code from the standard audio having to be 8khz to 16khz to keep with the snips audio so that it stays fast instead of having to convert the audio down from 16>8khz

For me I just placed all the files inside the snowboy/examples/python directory for convenience 

# Piwho Altered

i have altered and recompiled the java files and also the piwho python code to use 16khz and not 8khz to keep inline with snips audio and so time is not wasted converting 16->8khz, keeps it fast
for piwho a min of 2 users is needed for it to work
i used the vad.py from piwho to create the audio files
i use folder name as persons name and within place their audio files

- \Base Folder
- \train.py
- --\Bob
- ------\ file1.wav 
- ------\ file2.wav 
- ------\ file3.wav
- --\Tim 
- ------\file1.wav 
- ------\file2.wav

i then use the train.py in the base folder to build the training data for piwho
two files are created speakers.txt and something like marf.Storage.TrainingSet.70016000.0.0.0.103.300.2.20.gzbin -these two files need to be with the hotword.py file


# turning on
I have stopped and disabled the snips-hotword server
sudo systemctl stop snips-hotword && sudo systemctl disable snips-hotword

alter the hotword.service file to the path of your hotword.py file
- copy the hotword.service file into the /lib/systemd/system/ folder and change to chmod 775
- reboot
- sudo systemctl enable hotword && sudo systemctl start -hotword

hotword starts a snips session using sessionStart and passing in the customData object the name of the person who said the hotword
![](https://github.com/oziee/hotword/blob/master/images/mqtt.jpg?raw=true)
