from raspalarm.keypad.monitor import monitor

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
        print 'Correct PW supplied!'
        mon.stop()
        print monitor.running()
    def cbnok(mon):
        print 'Wrong PW supplied!'
    enable(cbok, cbnok)
    try:
        while monitor.running():
            pass
    finally:
        disable()
