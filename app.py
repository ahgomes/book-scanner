from flask import Flask, render_template, request, send_file
from flask_mysqldb import MySQL

from uuid import uuid4 as uuid
import csv
import json

from book_scanner import search

app = Flask(__name__)

app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root"
app.config["MYSQL_DB"] = "library"

mysql = MySQL(app)
headers = []
row_count = 0

# request separator
SEPARATOR = ';;'

# response message
BOOK_NOT_FOUND = 'BOOK NOT FOUND'

# ----------------------------
# SQL ACCESS
# ----------------------------
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

# ----------------------------
# DATA FORMATTING
# ----------------------------
def grab_header_names(headers):
    return [h[0] for h in headers]

def grab_public_headers(headers):
    return headers[2:]

# convert headers from mysql tuple to html<th/> string format
def format_headers():
    def upper(str:str):
        return ''.join(' ' + c if c.isupper() else c for c in str).upper()
    
    return list(map(upper, grab_header_names(headers)))

# convert data from json list to mysql string format
def prep_add_data(headers, data):
    def format(c):
        ((h, t), d) = c 
        if isinstance(d, int): d = str(d)
        if isinstance(d, list): d = ', '.join(d)
        if (d:=d.strip()) == '-' or len(d) < 1 : return 'null'
        if t != 'int': return f'"{d}"'
        return d
         
    return grab_header_names(headers), list(map(format, zip(headers, data)))

# convert data from request string to mysql string format
def prep_update_data(headers, data):
    data = data.split(SEPARATOR)

    def format(c):
        ((h, t), d) = c 
        if (d:=d.strip()) == '-' or len(d) < 1 : return f'{h}=null'
        if t != 'int': return f'{h}="{d}"'
        return f'{h}={d}'
         
    return list(map(format, zip(headers, data)))

# ----------------------------
# ROUTE HANDLING
# ----------------------------
@app.get('/')
def index():
    get_headers()
    return render_template('index.html')

@app.get('/table')
def table():
    data = sql('SELECT * FROM book')
    
    global row_count
    row_count = len(data) 

    return render_template('table.html', headers=format_headers(), data=sorted(data, key=lambda row: row[1]))

@app.put('/table')
def update_table():
    data = request.form.to_dict()['data']
    print(data)
    cols = prep_update_data(headers, data)

    # TODO: add validation
    
    sql(f'''
        UPDATE book
        SET {', '.join(cols[1:])}
        WHERE {cols[0]} ''')
    
    return ('', 200)

@app.delete('/table')
def del_row():
    data = request.form.to_dict()['data'].split(SEPARATOR)
    sql(f'''
        DELETE FROM book
        WHERE bookId="{data[0]}" ''')
    return ('', 200)

@app.post('/table')
def add_row():
    data = request.form.to_dict()
    
    book = data.get('book')
    if book == BOOK_NOT_FOUND: book = None
    if book:
        book = json.loads(book)
        cols, vals = prep_add_data(grab_public_headers(headers), book)
        print(book)

    def dequote(l):
        return list(map(lambda s: s.replace('"', ''), l))

    global row_count
    row_count += 1
    row = [uuid(), row_count] + (dequote(vals) if book else [None for _ in grab_public_headers(headers)])

    sql(f'''
        INSERT INTO book (bookId, listIndex {',' + ','.join(cols) if book else ''})
        VALUES ("{row[0]}", {row[1]} {',' + ','.join(vals) if book else ''}) ''')
    
    return render_template('row.html', row=row)

@app.get('/csv')
def get_csv():
    data = sql('SELECT * FROM book')
    path = 'books.csv'
    with open(path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(format_headers())
        csvwriter.writerows(sorted(data, key=lambda row: row[1]))
    return send_file(path, as_attachment=True)

@app.get('/book')
def get_book():
    isbn = request.args.to_dict()['isbn'].strip()
    
    if isbn == '': 
        found = False
    else:
        found, data = search(isbn)

    if not found: 
        return (BOOK_NOT_FOUND, 404)
    
    keys = grab_header_names(grab_public_headers(headers))
    data = data['items'][0]['volumeInfo']
    data = [data[k] if k != 'isbn' else isbn for k in keys]
    
    return (data, 200)

@app.route('/vid')
def vid():
    return render_template('video.html', data='hello')

# ----------------------------
# RUN APP
# ----------------------------
if __name__ == '__main__':
    app.run(host='localhost',port=3000, debug=True, threaded=True)
    