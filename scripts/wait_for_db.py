import sys
import time
import psycopg2
from psycopg2 import OperationalError

def wait_for_db():
    while True:
        try:
            conn = psycopg2.connect(
                dbname='umi',
                user='postgres',
                password='postgres',
                host='localhost',
                port='5432'
            )
            conn.close()
            print('\nDatabase is ready!')
            break
        except OperationalError:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1)

if __name__ == '__main__':
    print('Waiting for database...')
    wait_for_db() 