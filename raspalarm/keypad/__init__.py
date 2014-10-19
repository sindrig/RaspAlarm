import logging

from raspalarm.keypad.monitor import monitor

logger = logging.getLogger(__name__)

def disable():
    monitor.stop()

def enable(cbok, cbnok):
    '''
        callback is called when user submits the
        correct passcode
    '''
    monitor.start(cbok, cbnok)

if __name__ == '__main__':
    done = False
    def cbok(mon):
        logger.debug('Correct PW supplied!')
        mon.stop()

    def cbnok(mon):
        logger.debug('Wrong PW supplied!')

    enable(cbok, cbnok)
    try:
        while monitor.running():
            pass
    finally:
        disable()
