import requests
import csv

from pyzbar.pyzbar import decode

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2

def get_list(b, q):
    c = b.get(q)
    if c: 
        return ', '.join(c)
    else: 
        return None

fields = {
    'Title': lambda b: b.get('title'), 
    'Subtitle': lambda b: b.get('subtitle'), 
    'Authors': lambda b: get_list(b, 'authors'), 
    'ISBN': lambda _: '', 
    'Language': lambda b: b.get('language'), 
    'Published Date': lambda b: b.get('publishedDate'),
    'Genre': lambda b: get_list(b, 'category'),
}
schema = list(fields.keys())
rows = {}

def export():
    with open('books.csv', 'a', newline='') as csvfile:
        csvwriter = csv.DictWriter(csvfile, fieldnames=schema)
        if False: csvwriter.writeheader()
        csvwriter.writerows(rows.values())

def insert(isbn, data): 
    format = lambda d: d if d else '-'
    formated = list(map(lambda g: format(g(data)), fields.values()))
    rows[isbn] = { schema[i]: formated[i] for i in range(len(schema)) }
    rows[isbn]['ISBN'] = isbn
    table.insert('', tk.END, values=list(rows[isbn].values()))

def search(isbn):
    url = 'https://www.googleapis.com/books/v1/volumes?q=isbn:' + isbn
    res = requests.get(url)
    data = res.json()
    found = data['totalItems'] > 0 
    
    return found, data

def scan_video(frame):
    for code in decode(frame):
        isbn = code.data.decode('utf-8')
        success,data = search(isbn)
        if success: 
            if (r := rows.get(isbn)): 
                break
            insert(isbn, data['items'][0]['volumeInfo'])

def show_table():
    table = ttk.Treeview(win, columns=schema, show='headings') 
    for h in schema:
        table.heading(h, text=h)    
    table.grid(row=1)
    return table

def show_video():
    _, frame = cap.read()
    
    scan_video(frame)

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    img = Image.fromarray(frame)
    photo = ImageTk.PhotoImage(image=img)
    feed = tk.Label(win, height=200, width=300, image=photo)
    feed.image = photo
    feed.grid(row=0)

    win.after(10, show_video) 
    
if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    
    win = tk.Tk()
    
    feed = tk.Label(win).grid(row=0, columnspan=3)
    show_video()
    
    table = show_table()
    

    win.mainloop()

    cap.release()
    cv2.destroyAllWindows()
    export()
