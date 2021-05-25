from sqlite3 import Error

from core.db import init_connection


class ConnectionSql:

    def __init__(self,
                 path: str):
        self.connection = init_connection(path)

    def execute_query(self, query: str):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()
        except Error as e:
            print(f"The error '{e}' occurred")
