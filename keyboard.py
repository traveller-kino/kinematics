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

def reflectedOutput():
    modifierInformation = dict()
    """
        We need to check the previous vkc, and if it is a modifier, we need to keep going back until we find the last printable character
        Also need to check if CAPS is activated
        Non-printing modifiers: CTRL, ALT, WIN, FN (162|163|164|165|91|9|27|112|113|114|115|116|117|118|119|120|121|122|123|124)
        Printing modifiers: SHIFT (160|161)
        Note: SHIFT can be part of a non-printing modifier sequence, e.g. CTRL + SHIFT + ALT + WIN + L (is this Tony Hawk's Pro Keyboarder?)

        Customization drivers like Capsicain could very well mean that the user has non-printing sequences of their own, but that is beyond the scope atm
    """
    """
        Need to experimentally obtain vkcs for modifier keys, including left/right variants, and F keys
    """
    pass

class Manager:
    def __init__(self, csvFiles, csvWriters):
        self.keytimes = [time.perf_counter()] # Note: Windows may reduce the precision to as low as 20ms based on various factors.
        self.scancodes = [0]
        self.utfoutput = [0]
        self.csvFiles = csvFiles
        self.csvWriters = csvWriters
        self.capslock = False # No reasonable way to determine if caps lock is active, so assume it is initially off.
        self.shifted = None # TODO: Shift can be held in for multiple key presses without being logged. Should this be converted into a point-in-time check?
        # TODO: track release events for SHIFT, and also implement intra-keystroke timings
        # https://pynput.readthedocs.io/en/latest/keyboard.html

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

        # Update shift modifier after writing, so that we don't need to inspect the scancodes list
        if scanCode == 160 or scanCode == 161: self.shifted = True
        else: self.shifted = False

        if len(self.scancodes) % 10 == 0: self.csvFiles[0].flush()
        print(record)

scanCodeRecordHeaders = ["Timestamp", "Delta", "PreviousScanCode", "ScanCode"]
scanCodeCsv = open('scanCodeRecord.csv', 'a', newline='')
scanCodeWriter = csv.writer(scanCodeCsv, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL )

print('"Timestamp","Delta","PreviousScanCode","ScanCode"')

timer = Manager([scanCodeCsv, None], [scanCodeWriter, None])
with Listener(on_press=timer.press) as listener:
    listener.join()

scanCodeCsv.close()