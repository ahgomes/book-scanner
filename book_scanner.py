import requests
import csv

from pyzbar.pyzbar import decode
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

rows = {}

def export():
    with open('books.csv', 'w') as csvfile:
        csvwriter = csv.DictWriter(csvfile, fieldnames=list(fields.keys()))
        csvwriter.writeheader()
        csvwriter.writerows(rows.values())

def insert(isbn, data): 
    formated = list(map(lambda g: g(data), fields.values()))
    schema = list(fields.keys())
    rows[isbn] = { schema[i]: formated[i] for i in range(len(schema)) }
    rows[isbn]['ISBN'] = isbn

def search(isbn):
    url = 'https://www.googleapis.com/books/v1/volumes?q=isbn:' + isbn
    res = requests.get(url)
    data = res.json()
    found = data['totalItems'] > 0 
    
    return found, data

def main():
    cap = cv2.VideoCapture(0)
    found = False
    count = 0
    while not found:
        _, frame = cap.read()
        for code in decode(frame):
            isbn = code.data.decode('utf-8')
            success,data = search(isbn)
            if success: 
                if (r := rows.get(isbn)): 
                    print(r['Title'] + ' already added')
                    break
                insert(isbn, data['items'][0]['volumeInfo'])
                count += 1
                print(count)

        cv2.imshow('Scan ISBN CODE', frame)
        if cv2.waitKey(1) == ord('q'):
            cv2.destroyAllWindows()
            break
    export()

if __name__ == '__main__':
    main()
