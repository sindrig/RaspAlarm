from matrix_keypad import RPi_GPIO
from raspalarm.keypad import GPIO

def digit(kp):
    dp = None
    while dp is None:
        dp  = kp.getKey()
    return dp

if __name__=='__main__':
    kp = GPIO.Keypad()

    kp.COLUMN = [25, 8, 7]
    kp.ROW = [10, 9, 11, 24]
    taken = []
    while 1:
        try:
            d = digit(kp)
            if not d in taken:
                taken.append(d)
        except KeyboardInterrupt:
            print taken
            kp.exit()
            break
