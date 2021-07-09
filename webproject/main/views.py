import os
import math
import time

import cv2
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.http.response import StreamingHttpResponse
import bcrypt
import pickle
import face_recognition
import datetime
from sklearn import neighbors

from .models import User, Person, Detected
from .camera import VideoCamera

from face_recognition.face_recognition_cli import image_files_in_folder

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create your views here.
def index(request):
    return render(request, 'session/login.html')


def addUser(request):
    return render(request, 'home/add_user.html')


def logout_view(request):
    # Close the session and logout the user
    logout(request)
    messages.add_message(request, messages.INFO, "Successfully logged out")
    return redirect(index)


def login_view(request):
    return render(request, 'session/login.html')


def saveUser(request):
    # Check the user's input
    errors = User.objects.validator(request.POST)
    err_msg = ''

    # Load error message
    for tag, error in errors.items():
        for msg in error:
            err_msg += tag + ": " + msg + "<br>"

    # Display error message if it was not empty
    # Redirect user back to Create User Page
    if err_msg:
        messages.error(request, err_msg)
        return redirect(addUser)

    # Check the email whether already have an account
    # Redirect user back to Create User Page
    input_email = request.POST['email']
    if User.objects.filter(email=input_email).exists():
        messages.add_message(request, messages.INFO, 'User already exist')
        return redirect(addUser)

    # Salt and Hash process of the user's password
    hashed_password = bcrypt.hashpw(request.POST['password'].encode('utf-8'), bcrypt.gensalt()).decode()

    # Create entry for database
    user = User.objects.create(
        first_name=request.POST['first_name'],
        last_name=request.POST['last_name'],
        email=request.POST['email'],
        password=hashed_password)

    # Save the entry into database
    user.save()

    # Show message and redirect to Login Page
    messages.add_message(request, messages.INFO, 'User successfully added')
    return redirect(index)


def checkUsers(request):
    try:
        # Get the user id from current session
        current_user = User.objects.get(id=request.session['id'])

        # Proceed to delete the delete user page
        if current_user.id is not None:
            return render(request, 'home/del_users.html')
    except:
        # Exception: No user logged in currently
        messages.error(request, 'Oops, There are no user currently logged in')
        return redirect(index)


def delUser(request):
    try:
        # Get the User object from User Class by id
        current_user = User.objects.get(id=request.session['id'])
        # Get user's input (password) from POST
        check_password = request.POST['password'].replace(" ", "")  # remove whitespace

        # Get the saved password from User object
        current_hashed_ps = current_user.password

        # Check the password
        if bcrypt.checkpw(check_password.encode(), current_hashed_ps.encode()):
            # Logout the user and delete the user account
            logout(request)
            messages.add_message(request, messages.INFO, "Successfully logged out and delete the account")
            current_user.delete()
            return redirect(index)
        else:
            # Redirect to that page as wrong password was detected
            messages.error(request, 'Oops, Wrong password, please try a different password')
            return redirect(checkUsers)
    except:
        # Exception: No user logged in currently
        messages.error(request, 'Oops, There are no user currently logged in')
        return redirect(index)


def login(request):
    # Get user's input (email & password) from POST
    input_email = request.POST['login_email'].replace(" ", "")  # remove whitespace
    input_pass = request.POST['login_password'].replace(" ", "")  # remove whitespace

    # Check the user's account whether it was a valid account
    if User.objects.filter(email=input_email).exists():
        # Get the User object from User Class by email and get the password from it
        user = User.objects.filter(email=input_email)[0]
        hashed_ps = user.password

        # Check the password
        if bcrypt.checkpw(input_pass.encode(), hashed_ps.encode()):
            # Create a session in the request
            request.session['id'] = user.id
            request.session['name'] = user.first_name
            request.session['surname'] = user.last_name
            messages.add_message(request, messages.INFO,
                                 'Welcome to facial recognition system ' + user.first_name + ' ' + user.last_name)
            return redirect(success)
        else:
            # Redirect to that page as wrong password was detected
            messages.error(request, 'Oops, Wrong password, please try a different one')
            return redirect(index)
    else:
        # Redirect it to the page as no such user id in the database
        messages.error(request, 'Oops, That user id do not exist')
        return redirect(index)


def success(request):
    try:
        user = User.objects.get(id=request.session['id'])
        persons = Person.objects.filter(user_id=user);
        context = {
            "user": user,
            "persons": persons
        }
        return render(request, 'home/welcome.html', context)

    except:
        # Redirect it to the page as no logged in user currently
        messages.error(request, 'Oops, There are no user currently logged in')
        return redirect(index)


def video_stream(request):
    try:
        user = User.objects.get(id=request.session['id'])
        base_save_dir = os.path.join(BASE_DIR, "app/facerec/models")
        save_path = os.path.join(base_save_dir, str(user.id))
        file_exist = os.path.isfile(os.path.join(save_path, "trained_model.clf"))

        if file_exist:
            return render(request, 'home/video_stream.html')
        else:
            messages.add_message(request, messages.INFO, "No person images being trained!")
            return redirect(success)
    except:
        # Redirect it to the page as no logged in user currently
        messages.error(request, 'Oops, There are no user currently logged in')
        return redirect(index)


def gen(camera, request):
    while True:
        frame = camera.get_frame(request)
        if frame is not None:
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            continue


def video_feed(request):
    return StreamingHttpResponse(gen(VideoCamera(), request),
                                 content_type='multipart/x-mixed-replace; boundary=frame')


def addKnownPerson(request):
    try:
        # Get the user id from current session
        current_user = User.objects.get(id=request.session['id'])

        # Proceed to delete the add known person page
        if current_user.id is not None:
            return render(request, 'home/add_known_person.html')
    except:
        # Exception: No user logged in currently
        messages.error(request, 'Oops, There are no user currently logged in')
        return redirect(index)


def saveKnownPerson(request):
    if request.method == 'POST':
        # Get the user object with the user id from current session
        user = User.objects.get(id=request.session['id'])
        # Get the person name from the POST
        known = Person.objects.filter(user_id=user.id).filter(name=request.POST["name"])

        if known.exists():
            # Redirect the user back to same page as the person already exists.
            messages.error(request, "Persons with that name already exists")
            return redirect(addKnownPerson)
        else:
            # Create an entry into the Person class
            person = Person.objects.create(
                user_id=user,
                name=request.POST["name"],
            )
            person.save()
            # Redirect to the view person page to view recently added person.
            messages.add_message(request, messages.INFO, "Successfully added new known persons")
            return redirect(viewKnownPerson)


def viewKnownPerson(request):
    try:
        # Get the user id from current session
        current_user = User.objects.get(id=request.session['id'])

        # Proceed to delete the view known person page
        if current_user.id is not None:
            person = Person.objects.filter(user_id=current_user.id);
            context = {
                "persons": person
            }
            return render(request, 'home/view_known_persons.html', context)
    except:
        # Exception: No user logged in currently
        messages.error(request, 'Oops, There are no user currently logged in')
        return redirect(index)


def delPerson(request, person_id):
    # Get the user object with the user id from current session
    user = User.objects.get(id=request.session['id'])
    # Filter the person objects under that user_id
    known = Person.objects.filter(user_id=user.id).get(id=person_id)

    # Define the path to the file that store the image
    base_dir = os.path.join(BASE_DIR, "app/facerec/dataset")
    user_dir = os.path.join(base_dir, str(user.id))
    person_dir = os.path.join(user_dir, str(known.name))

    # Delete all the files inside the folder
    if os.path.exists(person_dir):
        filenames = os.listdir(person_dir)

        for file in filenames:
            path = os.path.join(person_dir, file)
            os.remove(path)

        os.rmdir(person_dir)
        # Train the classifier after file removal
        trainer(user.id)
        messages.add_message(request, messages.INFO, 'Re-Training was completed!')
    # Delete the person object from the database and redirect to view person page
    known.delete()
    return redirect(viewKnownPerson)


def detectImage(request):
    img_counter = 0
    if request.method == 'POST':
        # Get the selection of images from POST
        value = request.POST['selection']
        # Get the user object with the user id from current session
        user = User.objects.get(id=request.session['id'])
        # Filter the person objects under that user_id
        known = Person.objects.filter(user_id=user.id).get(name=value)
        # Indicate the number of images failed to upload
        err_1 = 0
        err_2 = 0

        # Create User Folder
        base_DIR = os.path.join(BASE_DIR, "app/facerec/dataset")
        base_DIR = os.path.join(base_DIR, str(user.id))
        try:
            os.mkdir(base_DIR)
        except FileExistsError:
            pass
        number_of_photo = 0
        # Load the image file into array
        myfiles = request.FILES.getlist('image')
        for myfile in myfiles:
            # Check the number of faces appeared in the image
            image = face_recognition.load_image_file(myfile)
            X_face_locations = face_recognition.face_locations(image)
            if len(X_face_locations) == 0:
                err_1 += 1
            elif len(X_face_locations) > 1:
                err_2 += 1
            else:
                # Create Person Folder
                DIR = os.path.join(base_DIR, known.name)
                try:
                    os.mkdir(DIR)
                except FileExistsError:
                    img_counter = len(os.listdir(DIR))
                # Save the upload image in the directory
                fs = FileSystemStorage(DIR)
                filename = fs.save(myfile.name, myfile)
                img_counter += 1
                number_of_photo = len(os.listdir(os.path.join(base_DIR, known.name)))

    # Train the classifier if one or more new images was uploaded
    if img_counter != 0 and number_of_photo >= 5:
        trainer(user.id)
        messages.add_message(request, messages.INFO,
                             'Successfully uploaded {} images. Training was completed!'.format(str(img_counter)))
    elif number_of_photo < 5:
        messages.add_message(request, messages.INFO, 'Successfully uploaded {} images. Need {} images to start the '
                                                     'training. '.format(str(img_counter), (5-number_of_photo)))
    if err_1 != 0:
        messages.error(request, 'Oops, There are no face appear in the image uploaded')
    if err_2 != 0:
        messages.error(request, 'Oops, There are more than 1 face appear in the image uploaded')
    return redirect(success)


def train(train_dir, model_save_path=None, n_neighbors=None, knn_algo='ball_tree'):
    X = []
    y = []

    # Loop through each person in the training set
    for class_dir in os.listdir(train_dir):
        if not os.path.isdir(os.path.join(train_dir, class_dir)):
            continue

        # Loop through each training image for the current person
        for img_path in image_files_in_folder(os.path.join(train_dir, class_dir)):
            image = face_recognition.load_image_file(img_path)
            face_bounding_boxes = face_recognition.face_locations(image)

            if len(face_bounding_boxes) != 1:
                #If there are no people (or too many people) in a training image, skip the image.
                pass
            else:
                # Add face encoding for current image to the training set
                X.append(face_recognition.face_encodings(image, known_face_locations=face_bounding_boxes)[0])
                y.append(class_dir.split('_')[0])

    # Determine how many neighbors to use for weighting in the KNN classifier
    if n_neighbors is None:
        n_neighbors = int(round(math.sqrt(len(X))))

    # Create and train the KNN classifier
    knn_clf = neighbors.KNeighborsClassifier(n_neighbors=n_neighbors, algorithm=knn_algo, weights='distance')
    knn_clf.fit(X, y)

    # Save the trained KNN classifier
    modelfile_save_path = os.path.join(model_save_path, "trained_model.clf")
    if modelfile_save_path is not None:
        with open(modelfile_save_path, 'wb') as f:
            pickle.dump(knn_clf, f)

    return knn_clf


def trainer(user_id):
    # Define the file path to get the training image
    # Also define the path to save the trained classifier
    base_train_dir = os.path.join(BASE_DIR, "app/facerec/dataset")
    base_save_dir = os.path.join(BASE_DIR, "app/facerec/models")
    train_dir = os.path.join(base_train_dir, str(user_id))
    save_path = os.path.join(base_save_dir, str(user_id))

    try:
        os.mkdir(save_path)
        print("Directory ", str(user_id), " Created ")
    except FileExistsError:
        print("Directory ", str(user_id), " already exists")

    if os.listdir(train_dir):
        classifier = train(train_dir, model_save_path=save_path, n_neighbors=3)
    else:
        os.remove(os.path.join(save_path, "trained_model.clf"))


def detected(request):
    if request.method == 'GET':
        user_id = request.session['id']
        date_formatted = datetime.datetime.today().date()
        date = request.GET.get('search_box', None)

        if date is not None:
            try:
                date_selected = datetime.datetime.strptime(date, "%Y-%m-%d").date()
                if date_selected <= date_formatted:
                    date_formatted = date_selected
                else:
                    messages.error(request, 'Oops, the date select was in the future.')
            except ValueError:
                print("Enter Valid datetime format")

        det_list = Detected.objects.filter(user_id=user_id).filter(time_stamp__date=date_formatted).order_by(
            'time_stamp').reverse()
        context = {
            'det_list': det_list,
            'date': date_formatted
        }
    return render(request, 'home/detected.html', context)