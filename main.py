import subprocess
import sys
import time


def run():
    N = int(input("\nEnter number of nodes :"))
    for i in range(N):
        command = "python3 nodev2.py {} {}".format(i, N)
        subprocess.Popen(
            ['osascript', '-e', 'tell application "System Events" to keystroke "`" using {control down, shift down}'])
        time.sleep(0.5)
        print("Executing command : ", command)
        subprocess.Popen(
            ['osascript', '-e', f'tell application "System Events" to tell process "Visual Studio Code" to keystroke "{command}\\n"'])
        time.sleep(0.5)


def stop():
    sys.exit()


function = {
    1: run,
    2: stop
}

while True:
    choice = int(input("\n\n1)RUN \n2)EXIT \n\nCOMMAND : "))
    function[choice]()
