import face_recognition
import cv2
import sqlite3
import numpy as np
import logging

# Configure logging
logging.basicConfig(filename='logs/face_recognition.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_known_faces():
    conn = sqlite3.connect('DB/faces.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, encoding FROM faces")
    known_faces = []
    known_names = []
    for name, encoding_blob in cursor.fetchall():
        encoding = np.frombuffer(encoding_blob, dtype=np.float64)
        known_faces.append(encoding)
        known_names.append(name)
    conn.close()
    return known_faces, known_names

def recognize_faces():
    known_faces, known_names = load_known_faces()
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.error("Failed to capture frame")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.6)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_names[first_match_index]
                logging.info(f"Face recognized: {name}")

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow('Live Recognition', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    recognize_faces()