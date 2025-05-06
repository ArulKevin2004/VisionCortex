import face_recognition
import cv2
import sqlite3
import numpy as np
from datetime import datetime
import logging
import os

# Create logs directory if it doesn't exist
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

db_dir = 'DB'
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# Configure logging
logging.basicConfig(filename='logs/face_recognition.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def init_db():
    conn = sqlite3.connect('DB/faces.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS faces 
                     (id INTEGER PRIMARY KEY, name TEXT, encoding BLOB, timestamp TEXT)''')
    conn.commit()
    conn.close()

def register_face(name):
    init_db()
    conn = sqlite3.connect('DB/faces.db')
    cursor = conn.cursor()
    
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            logging.error("Failed to capture image")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, "Press 's' to save", (left, top-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow('Register Face', frame)

        if cv2.waitKey(1) & 0xFF == ord('s') and len(face_encodings) > 0:
            encoding_blob = np.array(face_encodings[0]).tobytes()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO faces (name, encoding, timestamp) VALUES (?, ?, ?)",
                         (name, encoding_blob, timestamp))
            conn.commit()
            logging.info(f"Face registered: {name} at {timestamp}")
            print(f"Face registered for {name}")
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    conn.close()

if __name__ == "__main__":
    register_face("TestUser")