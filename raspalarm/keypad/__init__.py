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
    def cbok():
        global done
        print 'Correct PW supplied!'
        done = True
    def cbnok():
        print 'Wrong PW supplied!'
    enable(cbok, cbnok)
    try:
        while not done:
            pass
    except KeyboardInterrupt:
        disable()
