import time
import pymysql

def wait_for_db():
    while True:
        try:
            conn = pymysql.connect(
                host='127.0.0.1',
                port=3306,
                user='climas_admin',
                password='climas',
                database='climasdb'
            )
            conn.close()
            print("Database is ready!")
            return
        except Exception as e:
            print("Waiting for database...")
            time.sleep(3)

if __name__ == '__main__':
    wait_for_db()