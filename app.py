from flask import Flask, render_template, request
from flask_mysqldb import MySQL

from uuid import uuid4 as uuid

app = Flask(__name__)

app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root"
app.config["MYSQL_DB"] = "library"

mysql = MySQL(app)
headers = []
row_count = 0

def sql(query):
    cur = mysql.connection.cursor()
    cur.execute(query)
    data = cur.fetchall()
    mysql.connection.commit()
    cur.close()
    return data

def get_headers():
    data = sql('''
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME='book' ''')
    
    global headers
    headers = [tup for tup in data]

    return headers

def format_headers(headers):
    def upper(str:str):
        return str.replace('_', ' ').upper()
    
    return list(map(upper, [h[0] for h in headers]))

def prep_update_data(data):
    data = data.split(',')

    def format(c):
        ((h, t), d) = c 
        if (d:=d.strip()) == '-' or len(d) < 1 : return f'{h}=null'
        if t != 'int': return f'{h}="{d}"'
        return f'{h}={d}'
         
    return list(map(format, zip(headers, data)))

@app.get('/')
def index():
    get_headers()
    return render_template('index.html')

@app.get('/table')
def table():
    data = sql('SELECT * FROM book')
    
    global row_count
    row_count = len(data) 

    return render_template('table.html', headers=format_headers(headers), data=sorted(data, key=lambda row: row[1]))

@app.post('/table')
def update_table():
    data = request.form.to_dict()['data']
    cols = prep_update_data(data)

    # TODO: add validation
    
    sql(f'''
        UPDATE book
        SET {', '.join(cols[1:])}
        WHERE {cols[0]} ''')
    
    return ('', 204)

@app.post('/table/add')
def add_row():
    global row_count
    row_count += 1
    row = [uuid(), row_count] + [None for _ in headers[2:]]

    sql(f'''
        INSERT INTO book (book_id, list_index)
        VALUES ("{row[0]}", {row[1]}) ''')
    
    return render_template('row.html', row=row)

@app.route('/vid')
def vid():
    return render_template('video.html', data='hello')

if __name__ == '__main__':
    app.run(host='localhost',port=3000, debug=True, threaded=True)
    