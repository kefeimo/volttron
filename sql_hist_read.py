import sqlite3

try:
    conn = sqlite3.connect('/home/kefei/.volttron_remote/agents/'
                           'a83ea45e-88f3-4c05-baf3-65994fa4a153/sqlhistorianagent-4.0.0/data/'
                           'historian_test.sqlite')
    print(conn)
    cursor = conn.cursor()
except Exception as e:
    print(e)


def get_tables():
    """
    >> [('data',), ('topics',)]
    """

    statement = \
'''
SELECT 
    name
FROM 
    sqlite_schema
WHERE 
    type ='table' AND 
    name NOT LIKE 'sqlite_%';
'''

    rows = cursor.execute(statement).fetchall()
    print(rows)


def get_data():
    statement = \
        '''
        SELECT 
            *
        FROM 
            data
        '''

    rows = cursor.execute(statement).fetchall()
    print(rows)


def get_topics():
    statement = \
        '''
        SELECT 
            *
        FROM 
            topics
        '''

    rows = cursor.execute(statement).fetchall()
    print(rows)


if __name__ == "__main__":
    get_tables()
    get_data()
    # get_topics()
