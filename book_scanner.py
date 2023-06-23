import requests

from pyzbar.pyzbar import decode
import cv2

def search(isbn):
    url = "https://www.googleapis.com/books/v1/volumes?q=isbn:" + isbn
    res = requests.get(url)
    data = res.json()
    found = data["totalItems"] > 0 
    
    return found, data

def main():
    cap = cv2.VideoCapture(0)
    found = False
    while not found:
        _, frame = cap.read()
        for code in decode(frame):
            success,data = search(code.data.decode('utf-8'))
            if success: 
                print(data)
                found = True

        cv2.imshow("Scan ISBN CODE", frame)
        if cv2.waitKey(1) == ord("q"):
            break

if __name__ == "__main__":
    main()
