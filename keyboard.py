import sqlite3
import pynput, time
from time import perf_counter
from pynput.keyboard import Key,Listener
from pathlib import Path
import shutil
import csv

# Check if there is already a profile, if not, copy the DB prototype
dbFile = Path("./keyboard.db")
if not dbFile.is_file():
    shutil.copy2("./keyboard.db.prototype", "./keyboard.db")

translationFile = open('./vkMappings.csv')
translationDict = csv.DictReader(translationFile, fieldnames=['key', 'vkCode'], quotechar='"', delimiter=',', escapechar="\\")
memDict = dict()
counter = 0
for row in translationDict:
    memDict[0x20 + counter] = row['vkCode']
    counter += 1
nMemDict = dict()
counter = 0
for row in memDict: # Invert, because manipulating the CSV is damn near impossible
    nMemDict[memDict[row]] = 0x20 + counter
    counter += 1
memDict = nMemDict

translationFile.close()
connection = sqlite3.connect('keyboard.db')
cursor = connection.cursor()

""" TODO: 
    * Need to keep track of the raw keystrokes (virtual key codes) AND the outcome (printed UTF-8)
    * Include key down / key up timings, as this is kinematically significant as well
    * Change the even/odd design to an explicit ring buffer
    * Dump outputs to a CSV, because an n^2 table is too impractical
"""
class KeyCorrelator:
    RIX = 0
    def __init__(self):
        self.evenTimer = 0
        self.evenLastKey = 'NULL'
        self.oddTimer = 0
        self.oddLastKey = 'NULL'

    def press(self, key):
        if KeyCorrelator.RIX % 2 == 0:

            try:
                if key.vk < 0x00 or key.vk > 0xFFFF:
                    return
            except:
                if not (key.value.vk < 0x00 or key.value.vk > 0xFFFF):
                    key = chr(key.value.vk)
                    pass
                else: return
            self.evenTimer = time.perf_counter()
            self.evenLastKey = key

            diff = self.evenTimer - self.oddTimer
            if diff > 2.5: 
                KeyCorrelator.RIX += 1
                return
            print(str(self.oddLastKey) + "\t\t" + "=>" + "\t" + str(self.evenLastKey) + "\t\t" + str(diff))
            KeyCorrelator.RIX += 1
        else:
            
            try:
                if key.vk < 0x00 or key.vk > 0xFFFF:
                    return
            except:
                if not (key.value.vk < 0x00 or key.value.vk > 0xFFFF):
                    key = chr(key.value.vk)
                    pass
                else: return
            self.oddTimer = time.perf_counter()
            self.oddLastKey = key

            diff = self.oddTimer - self.evenTimer
            if diff > 2.5: 
                KeyCorrelator.RIX += 1
                return
            print(str(self.evenLastKey) + "\t\t" + "=>" + "\t" + str(self.oddLastKey) + "\t\t" + str(diff))
            KeyCorrelator.RIX += 1

timer = KeyCorrelator()
with Listener(on_press=timer.press) as listener:
    listener.join()

connection.commit()
connection.close()