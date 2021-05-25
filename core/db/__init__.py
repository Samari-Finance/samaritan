import sqlite3
from sqlite3 import Error


def init_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print(f'connected successfully to {path}')
    except Error as e:
        print(f'Connection error: {e}')
    return connection

