import sys

from raspalarm.temperature import db, reader

def insert_reading():
    '''
        Should be called periodically and inserts temperature reading
        to our database.
    '''
    logger.debug('Inserting reading...')
    database = db.Database()
    database.insert_reading(reader.read())


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        if arg == 'temp':
            insert_reading()
