# Dora-Robomaster

This project aims to use Dora to enhance the capabilities of a RoboMaster S1. 
Click here to see the [First presentation for dora-robomaster](https://docs.google.com/presentation/d/18jjlBskEOXih-jM1cYWa8fFOB9j8ltHgOx4vg5BSuk0/edit?usp=sharing)

### Getting Started

command to start the demo:

```bash
alias dora='dora-cli'
dora up
dora start graphs/dataflow.yml --attach
```

start the reaction lighting test:
`dora start graphs/reaction.yml --attach`


## Installation of the Robomaster S1 Hack

This guide is an updated version of the original [Robomaster S1 SDK Hack Guide](https://www.bug-br.org.br/s1_sdk_hack.zip) and is intended for use on a Windows 11 system.

### Prerequisites

Before you get started, you'll need the following:

- Robomaster S1 (do not update it to the latest version, as it may block the hack).
- [Robomaster App](https://www.dji.com/fr/robomaster-s1/downloads).
- [Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools). Simply unzip it and keep the path handy.
- A micro USB cable. If this guide doesn't work, there might be an issue with the cable, and you may need to replace it with one that supports data transfer.

### Instructions

1. Start the Robomaster App and connect the Robomaster S1 using one of the two options provided (via router or via Wi-Fi).
2. While connected, use a micro USB cable to connect the robot to the computer's USB port. You should hear a beep sound, similar to when you connect any device. (Please note that no other Android device should be connected via USB during this process).
3. In the Lab section of the app, create a new Python application and paste the following code:

   ```python
   def root_me(module):
       __import__ = rm_define.__dict__['__builtins__']['__import__']
       return __import__(module, globals(), locals(), [], 0)

   builtins = root_me('builtins')
   subprocess = root_me('subprocess')
   proc = subprocess.Popen('/system/bin/adb_en.sh', shell=True, executable='/system/bin/sh', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   ```

4. Run the code; there should be no errors, and the console should display **Execution Complete**
5. Without closing the app, navigate to the folder containing the Android SDK Platform-Tools and open a terminal inside it.
6. Run the ADP command `.\adb.exe devices `. If everything is working correctly, you should see output similar to this: ![image](https://github.com/Felixhuangsiling/Dora-Robomaster/assets/77993249/dc6368ec-052c-4b18-8fdc-0ec314adb073)
7. Execute the upload.sh script located in the folder `s1_SDK`.
8. Once everything has been executed, restart the S1 by turning it off and then back on. While it's booting up, you should hear two chimes instead of the usual single chime, indicating that the hack has been successful.




