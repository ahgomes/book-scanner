from flask import Flask, render_template, request
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root"
app.config["MYSQL_DB"] = "library"

mysql = MySQL(app)
headers = []

def get_headers():
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME='book'  ''')
    global headers
    headers = [tuple for tuple in cur]
    cur.close()
    return headers

def prep_data(data):
    if len(headers) < 1: get_headers()
    data = data.split(',')

    def format(c):
        ((h, t), d) = c 
        if (d:=d.strip()) == '-' or len(d) < 1 : return f'{h}=null'
        if t != 'int': return f'{h}="{d}"'
        return f'{h}={d}'
         
    return list(map(format, zip(headers, data)))

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/table')
def table():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM book')
    data = cur.fetchall()
    cur.close()
    return render_template('table.html', headers=[h[0] for h in get_headers()], data=data)

@app.post('/table')
def updateTable():
    data = request.form.to_dict()['data']
    cols = prep_data(data)
    
    sql = f'''
        UPDATE book
        SET {', '.join(cols[1:])}
        WHERE {cols[0]}
    '''
    cur = mysql.connection.cursor()
    cur.execute(sql)
    mysql.connection.commit()
    cur.close()

    return ('', 204)

@app.route('/vid')
def vid():
    return render_template('video.html', data='hello')

if __name__ == '__main__':
    app.run(host='localhost',port=3000, debug=True, threaded=True)
