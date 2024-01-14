import pynput, time
from time import perf_counter
from pynput.keyboard import Key,Listener
import csv

# from pathlib import Path
# import shutil

""" TODO: 
    * Need to keep track of the raw keystrokes (virtual key codes) AND the outcome (printed UTF-8)
    * Include key down / key up timings, as this is kinematically significant as well
"""
class Manager:
    def __init__(self, csvFiles, csvWriters):
        self.keytimes = [time.perf_counter()] # Note: Windows may reduce the precision to as low as 20ms based on various factors.
        self.scancodes = [0]
        self.utfoutput = [0]
        self.csvFiles = csvFiles
        self.csvWriters = csvWriters

    def press(self, key):
        isFnOrMod = None
        scanCode = None
        try:
            scanCode = key.vk
            isFnOrMod = False
        except AttributeError:
            scanCode = key.value.vk
            isFnOrMod = True
        
        currentPrecisionTime = time.perf_counter()
        if ( currentPrecisionTime - (self.keytimes[-1]) ) > 2.5:
            # Keystroke is stale. Associatively insert a "stub", so that analyzers know to dispose of as well.
            self.keytimes.append(currentPrecisionTime)
            self.scancodes.append(0)
            self.utfoutput.append(0)
            return
        
        self.keytimes.append(currentPrecisionTime)
        self.scancodes.append(scanCode)
        self.utfoutput.append(-1) # TODO: Implement functionality to determine what is actually being printed to the screen. e.g. if the previous key was shift, and this key is 'a', it should really be 'A', not 'a'.

        record = '"{}","{}","{}","{}"'.format(str(self.keytimes[-1]), str(self.keytimes[-1] - self.keytimes[-2]), str(self.scancodes[-2]), str(self.scancodes[-1]))
        self.csvWriters[0].writerow([str(self.keytimes[-1]), str(self.keytimes[-1] - self.keytimes[-2]), str(self.scancodes[-2]), str(self.scancodes[-1])])
        if len(self.scancodes) % 10 == 0: self.csvFiles[0].flush()
        print(record)

scanCodeRecordHeaders = ["Timestamp", "Delta", "PreviousScanCode", "ScanCode"]
scanCodeCsv = open('scanCodeRecord.csv', 'a', newline='')
scanCodeWriter = csv.writer(scanCodeCsv, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL )

print('"Timestamp","Delta","PrevScanCode","ScanCode"')

timer = Manager([scanCodeCsv, None], [scanCodeWriter, None])
with Listener(on_press=timer.press) as listener:
    listener.join()

scanCodeCsv.close()