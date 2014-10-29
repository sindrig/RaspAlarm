#!/usr/bin/python
# Work derived from matrix_keypad
# matrix_keypad on pypi: https://pypi.python.org/pypi/matrix_keypad

import RPi.GPIO as GPIO

class Keypad():
    def __init__(self, columnCount = 3):
        GPIO.setmode(GPIO.BCM)

        # CONSTANTS
        KEYPAD = [
            [1,2,3],
            [4,5,6],
            [7,8,9],
            ["*",0,"#"]
        ]
        self.COLUMN = [25, 8, 7]
        self.ROW = [10, 9, 11, 24]
        self.KEYPAD = {}
        for i, rp in enumerate(self.ROW):
            self.KEYPAD[rp] = {}
            for j, rc in enumerate(self.COLUMN):
                self.KEYPAD[rp][rc] = KEYPAD[i][j]

    def getKey(self):
        try:
            return self._getKey()
        finally:
            self.exit()

    def _getKey(self):

        # Set all columns as output low
        for pin in self.COLUMN:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # Set all rows as input
        for pin in self.ROW:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Scan rows for pushed key/button
        try:
            rowSel = [pin for pin in self.ROW if GPIO.input(pin) == 0][0]
        except IndexError:
            return

        # Convert columns to input
        for pin in self.COLUMN:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Switch the i-th row found from scan to output
        GPIO.setup(rowSel, GPIO.OUT)
        GPIO.output(rowSel, GPIO.HIGH)

        # Scan columns for still-pushed key/button
        try:
            colSel = [pin for pin in self.COLUMN if GPIO.input(pin) == 1][0]
        except IndexError:
            return

        # Return the value of the key pressed
        return self.KEYPAD[rowSel][colSel]

    def exit(self):
        # Reinitialize all rows and columns as input at exit
        for pin in self.COLUMN + self.ROW:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

if __name__ == '__main__':
    # Initialize the keypad class
    kp = Keypad()

    # Loop while waiting for a keypress
    digit = None
    lastDigit = None
    while 1:
        while digit == None or digit == lastDigit:
            digit = kp.getKey()

        # Print the result
        print digit
        lastDigit = digit
