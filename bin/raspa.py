#!/usr/bin/env python
import os
import sys
import datetime
import time

from raspalarm.conf import getLogger, settings
from raspalarm.temperature import db, reader
from raspalarm.web import serve_forever

logger = getLogger('CMD')

def insert_reading():
    '''
        Should be called periodically and inserts temperature reading
        to our database.
    '''
    logger.debug('Inserting reading...')
    database = db.Database()
    database.insert_reading(reader.read())

def create_graph():
    '''
        Creates a graph from all readings today
    '''
    from raspalarm.temperature import grapher
    fn = grapher.get_filename()
    now = datetime.datetime.now()
    midnight = datetime.datetime.combine(now.date(), datetime.time.min)
    connection = db.Database()
    data = connection.get_readings((midnight, now))
    x = []
    y = []
    for timestamp, temp in data:
        x.append(datetime.datetime.fromtimestamp(float(timestamp)))
        y.append(temp)
    print x, y
    grapher.create(x, y, fn)




if __name__ == '__main__':
    for arg in sys.argv[1:]:
        if arg == 'temp':
            insert_reading()
        if arg == 'graph':
            create_graph()
        if arg == 'web':
            serve_forever()
