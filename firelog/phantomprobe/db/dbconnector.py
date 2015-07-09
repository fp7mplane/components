import sqlite3
import re


class DBConnector():

    def __init__(self, dbfile):
        self.conn = sqlite3.connect(dbfile)

    def execute_query(self, query, tup=None):
        create = re.compile('create', re.IGNORECASE)
        select = re.compile('select', re.IGNORECASE)
        insert = re.compile('insert', re.IGNORECASE)
        update = re.compile('update', re.IGNORECASE)
        c = self.conn.cursor()
        if not tup:
            c.execute(query)
            if re.match(create, query) or re.match(update, query):
                self.conn.commit()
                return
            elif re.match(select, query):
                result = c.fetchall()
                return result
            elif re.match(insert, query):
                self.conn.commit()
                return c.lastrowid
            else:
                print("Query not supported. {0}".format(query))
                self.conn.commit()
        else:  # parameters in insert as tuple
            c.execute(query, tup)
            self.conn.commit()
            return c.lastrowid

    def close_conn(self):
        self.conn.close()
