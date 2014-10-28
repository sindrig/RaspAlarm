import sqlite3
import datetime

from raspalarm.conf import settings, getLogger

logger = getLogger(__name__)
CREATE_STATEMENT = '''CREATE TABLE IF NOT EXISTS temps(
temp REAL NOT NULL,
timestamp DATETIME default CURRENT_TIMESTAMP NOT NULL,
id integer primary key AUTOINCREMENT NOT NULL
);'''


class Database(object):
    def __init__(self):
        with sqlite3.connect(settings.DATABASE) as c:
            cur = c.cursor()
            cur.execute(CREATE_STATEMENT)
            c.commit()


    def _get_data(self, query, params=tuple(), single=False):
        with sqlite3.connect(settings.DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if single:
                res = cursor.fetchone()
                if res and len(res) == 1:
                    # Return only the value
                    res = res[0]
                return res
            else:
                res = cursor.fetchall()
                if res and len(res[0]) == 1:
                    # If we are selecting one column, turn the result into
                    # a list of values instead of list of one-item sized tuples
                    res = [r[0] for r in res]
                return res


    def insert_reading(self, temp):
        '''
            Saves a temperature reading in our shared database
        '''
        logger.debug('Inserting temparature reading: %0.3f', temp)
        with sqlite3.connect(settings.DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO temps (temp) VALUES (?)', (temp, ))
            conn.commit()
        logger.debug('Temperature reading inserted!')

    def get_readings(self, timerange=None):
        '''
            Gets all temperature values in timerange along with their
            timestamp. If timerange is not supplied it defaults to all
            readings.
        '''
        logger.debug(
            'Getting temperatures from timerange: %s', repr(timerange))
        if timerange:
            q = (
                'SELECT timestamp, temp FROM temps '
                'WHERE timestamp BETWEEN ? and ?'
            )
            return self._get_data(q, timerange)
        else:
            return self._get_data('SELECT timestamp, temp FROM temps')

    def get_latest_reading(self):
        logger.debug('Getting latest temperature reading')
        return self._get_data(
            'SELECT temp FROM temps ORDER BY timestamp DESC LIMIT 1',
            single=True
        )

if __name__ == '__main__':
    from raspalarm.temperature.reader import read
    db = Database()
    value = read()
    db.insert_reading(value)
    print db.get_latest_reading()
    rng = (
        datetime.datetime.now() - datetime.timedelta(minutes=1),
        datetime.datetime.now()
    )
    print db.get_readings(rng)
