import os
from django.core.mail import send_mail
from django.utils import timezone
import cv2
import pickle
import face_recognition
import datetime
from cachetools import TTLCache
from .models import User, Person, Detected
from faceregapp.settings import EMAIL_HOST_USER

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cache = TTLCache(maxsize=20, ttl=60)

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()

    def alive(self):
        return self.video.isOpened()

    def get_frame(self, request):
        # Get the user id from current session
        user_id = request.session['id']

        # Grab a single frame of video
        success, image = self.video.read()

        while not success:
            self.video = cv2.VideoCapture(0)
            success, image = self.video.read()

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(image, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_frame = small_frame[:, :, ::-1]

        # Perform face recognition on the image and get classifier from the user
        base_save_dir = os.path.join(BASE_DIR, "app/facerec/models")
        save_path = os.path.join(base_save_dir, str(user_id))
        save_file = os.path.join(save_path, "trained_model.clf")

        predictions = predict(rgb_frame, model_path=save_file)

        for name, (top, right, bottom, left) in predictions:
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(image, (left, bottom - 25), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(image, name, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)

            # Make a detection record for the detected person
            identify(user_id, image, name)

        # Convert the raw images to JPEG format in order to display in the web application
        ret, jpeg = cv2.imencode('.jpg', image)
        cv2.waitKey(50)
        return jpeg.tobytes()


def identify(user_id, frame, name):
    # If person was detected within a period of time
    # Return to avoid multiple data entry in short amount of time
    if name in cache:
        return

    # Get current timestamp
    timestamp = datetime.datetime.now(tz=timezone.utc)
    unidentified = 'unknown'

    str_timestamp = ''.join(e for e in str(timestamp) if e.isalnum())

    # Mark the person name in cache as detected
    cache[name] = 'detected'

    # File path to save the image in the media folder
    path = 'detected/{}_{}.jpg'.format(name, str_timestamp)
    write_path = 'media/' + path
    save_path = os.path.join(BASE_DIR, write_path)
    status = cv2.imwrite(save_path, frame)

    # Create data entry for unidentified person
    if name.casefold() == unidentified.casefold():
        name = "Unknown"
        user = User.objects.get(id=user_id)
        user.detected_set.create(person_name=name, time_stamp=timestamp, photo=path)
        # Send email notification to the user
        sendemail(user.email)

    # Create data entry for recognized person
    else:
        user = User.objects.get(id=user_id)
        user.detected_set.create(person_name=name, time_stamp=timestamp, photo=path)


def predict(rgb_frame, knn_clf=None, model_path=None, distance_threshold=0.4):
    if knn_clf is None and model_path is None:
        raise Exception("Must supply knn classifier either thourgh knn_clf or model_path")

    # Load a trained KNN model (if one was passed in)
    if knn_clf is None:
        with open(model_path, 'rb') as f:
            knn_clf = pickle.load(f)

    # Load image file and find face locations
    X_face_locations = face_recognition.face_locations(rgb_frame, number_of_times_to_upsample=2)

    # If no faces are found in the image, return an empty result.
    if len(X_face_locations) == 0:
        return []

    # Find encodings for faces in the test iamge
    faces_encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=X_face_locations)

    # Use the KNN model to find the best matches for the test face
    closest_distances = knn_clf.kneighbors(faces_encodings, n_neighbors=1)
    are_matches = [closest_distances[0][i][0] <= distance_threshold for i in range(len(X_face_locations))]

    # Predict classes and remove classifications that aren't within the threshold
    return [(pred, loc) if rec else ("unknown", loc) for pred, loc, rec in
            zip(knn_clf.predict(faces_encodings), X_face_locations, are_matches)]


def sendemail(user_email):
    subject = 'Unidentified Person Detected'
    message = 'An unidentified person detected please be aware of it'
    message = 'An unidentified person detected please be aware of it'
    recepient = user_email
    send_mail(subject,
              message, EMAIL_HOST_USER, [recepient], fail_silently=False)