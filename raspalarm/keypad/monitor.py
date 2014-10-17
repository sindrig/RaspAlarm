import time
from threading import Thread

from raspalarm.keypad import GPIO

from raspalarm.conf import settings

class Monitor(Thread):
    '''
        A thread that monitors user input
    '''
    _running = True
    time_between_reset = 2  # Time until we disregard current input

    def __init__(self, passcode, callbackSuccess, callbackFail,
                 *args, **kwargs):
        self.passcode = passcode
        self.callbackSuccess = callbackSuccess
        self.callbackFail = callbackFail
        self.kp = GPIO.Keypad()

        super(Monitor, self).__init__(*args, **kwargs)

    def terminate(self):
        self._running = False

    def get_next_key(self):
        pressed_key = None
        start = time.time()
        while (
            pressed_key is None and
            (time.time() - start) < self.time_between_reset and
            self._running
        ):
            pressed_key = self.kp.getKey()
        print 'Got Key: %s' % pressed_key
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
                print len(current_code), len(self.passcode), done
                if done:
                    current_input = ''.join(
                        str(x) for x in current_code
                    ).rstrip('#')
                    if current_input == self.passcode:
                        self.callbackSuccess()
                    else:
                        self.callbackFail()
                    current_code = []
            else:
                current_code = []


class KeypadMonitor(object):

    def start(self, callbackSuccess, callbackFail):
        '''
            Starts monitoring user input from keypad. If the user supplies
            a right passphrase as described in settings.PASSCODE,
            callbackSuccess is called. If he supplies a wrong passphrase,
            callbackFail is called.
        '''
        self._monitoring = 1
        self.monitor = Monitor(
            passcode=settings.PASSCODE,
            callbackSuccess=self.wrap(callbackSuccess, True),
            callbackFail=self.wrap(callbackFail, False)
        )
        self.monitor.start()

    def wrap(self, func, do_stop):
        def wrapped():
            if do_stop:
                self.stop()
            return func()
        return wrapped

    def stop(self):
        '''
            Stops monitoring user input and kills our thread
        '''
        self.monitor.terminate()
        self._monitoring = 0
        self.monitor.join()

monitor = KeypadMonitor()
