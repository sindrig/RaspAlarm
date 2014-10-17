#!/usr/bin/python
# Disclaimer: This is not originally my work, I have modified it
# to suit my needs. All credit goes to Chris Crumpacker
# (chris@chriscrumpacker.com).
# matrix_keypad on pypi: https://pypi.python.org/pypi/matrix_keypad

import RPi.GPIO as GPIO
#import wiringpi

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

        # Set all columns as output low
        for pin in self.COLUMN:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # Set all rows as input
        for pin in self.ROW:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Scan rows for pushed key/button
        rowSel = -1
        for pin in self.ROW:
            tmpRead = GPIO.input(pin)
            if tmpRead == 0:
                rowSel = pin

        if not rowSel in self.ROW:
            self.exit()
            return

        # Convert columns to input
        for pin in self.COLUMN:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Switch the i-th row found from scan to output
        GPIO.setup(rowSel, GPIO.OUT)
        GPIO.output(rowSel, GPIO.HIGH)

        # Scan columns for still-pushed key/button
        colSel = -1
        for pin in self.COLUMN:
            tmpRead = GPIO.input(pin)
            if tmpRead == 1:
                colSel = pin

        if not colSel in self.COLUMN:
            self.exit()
            return

        # Return the value of the key pressed
        self.exit()
        return self.KEYPAD[rowSel][colSel]

    def _getKey(self):

        # Set all columns as output low
        for pin in self.COLUMN:
            wiringpi.pinMode(pin, wiringpi.OUTPUT)
            wiringpi.digitalWrite(pin, wiringpi.LOW)

        # Set all rows as input
        for pin in self.ROW:
            wiringpi.pinMode(pin, wiringpi.INPUT)
            wiringpi.pullUpDnControl(pin, wiringpi.PUD_UP)

        # Scan rows for pushed key/button
        rowSel = -1
        for pin in self.ROW:
            tmpRead = wiringpi.digitalRead(pin)
            if tmpRead == 0:
                rowSel = pin

        if not rowSel in self.ROW:
            self.exit()
            return

        # Convert columns to input
        for pin in self.COLUMN:
            wiringpi.pinMode(pin, wiringpi.INPUT)
            wiringpi.pullUpDnControl(pin, wiringpi.PUD_DOWN)

        # Switch the i-th row found from scan to output
        wiringpi.pinMode(rowSel, wiringpi.OUTPUT)
        wiringpi.digitalWrite(rowSel, wiringpi.HIGH)

        # Scan columns for still-pushed key/button
        colSel = -1
        for pin in self.COLUMN:
            tmpRead = wiringpi.digitalRead(pin)
            if tmpRead == 1:
                colSel = pin

        if not colSel in self.COLUMN:
            self.exit()
            return

        # Return the value of the key pressed
        self.exit()
        return self.KEYPAD[rowSel][colSel]

    def exit(self):
        # Reinitialize all rows and columns as input at exit
        for pin in self.COLUMN + self.ROW:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # wiringpi.pinMode(pin, wiringpi.INPUT)
            # wiringpi.pullUpDnControl(pin, wiringpi.PUD_UP)

if __name__ == '__main__':
    # Initialize the keypad class
    kp = keypad()

    # Loop while waiting for a keypress
    digit = None
    while digit == None:
        digit = kp.getKey()

    # Print the result
    print digit
