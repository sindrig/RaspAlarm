import logging
import time
from threading import Thread

from raspalarm.keypad import GPIO
from raspalarm.conf import settings

logger = logging.getLogger(__name__)


class Monitor(Thread):
    '''
        A thread that monitors user input
    '''
    _running = True
    time_between_reset = 2  # Time until we disregard current input

    callbackSuccess = None
    passcode = None
    callbackFail = None

    def __init__(self, *args, **kwargs):
        self.kp = GPIO.Keypad()
        super(Monitor, self).__init__(*args, **kwargs)

    def terminate(self):
        '''
            Stops monitoring user input
        '''
        self._running = False

    def get_next_key(self):
        '''
            Get the next key. If no key is supplied within
            self.time_between_reset we return None.
        '''
        pressed_key = None
        start = time.time()
        while (
            pressed_key is None and
            (time.time() - start) < self.time_between_reset and
            self._running
        ):
            pressed_key = self.kp.getKey()
        if pressed_key:
            logger.info('Got Key: %s' % pressed_key)
        while self.kp.getKey() is not None and self._running:
            # Wait until user releases the key
            pass
        return pressed_key

    def run(self):
        current_code = []
        while self._running:
            next_key = self.get_next_key()
            if next_key:
                current_code.append(next_key)
                done = False
                done = (
                    current_code[-1] == '#'
                    or
                    len(current_code) == len(self.passcode)
                )
                if done:
                    current_input = ''.join(
                        str(x) for x in current_code
                    ).rstrip('#')
                    if current_input == self.passcode:
                        self.callbackSuccess(self)
                    else:
                        self.callbackFail(self)
                    current_code = []
            else:
                current_code = []


    def start(self, callbackSuccess, callbackFail):
        '''
            Starts monitoring user input from keypad. If the user supplies
            a correct passphrase as described in settings.PASSCODE,
            callbackSuccess is called. If he supplies a wrong passphrase,
            callbackFail is called.
        '''
        self.passcode = settings.PASSCODE
        self.callbackSuccess = callbackSuccess
        self.callbackFail = callbackFail

        super(Monitor, self).start()

    stop = terminate

    def running(self):
        '''
            Getter for our private _running variable
        '''
        return self._running

monitor = Monitor()
