#!/usr/bin/env python
import datetime
import sqlite3

import reader

def add():
    temp = reader.read()
    if temp and temp > 3:
        with sqlite3.connect('/home/pi/tempgauge/temp.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO temps (temp) VALUES (?)', (temp, ))
            conn.commit()
            print 'Added temp @ %s' % datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        


if __name__ == '__main__':
    add()
