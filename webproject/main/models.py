import os
import re
from django.db import models


# Create your models here.
class UserManager(models.Manager):
    def validator(self, postData):
        errors = {"first_name": [],
                  "last_name": [],
                  "password": [],
                  "email": []}

        firstname = postData['first_name'].replace(" ", "")
        lastname = postData['last_name'].replace(" ", "")
        password = postData['password'].replace(" ", "")
        email = postData['email']

        # Check whether it is contain alphabet only
        if not firstname.isalpha():
            errors['first_name'].append('Pls enter alphabet')
        # Check the number of character
        if len(firstname) < 2:
            errors['first_name'].append('First name can not be shorter than 2 characters')

        # Check whether it is contain alphabet only
        if not lastname.isalpha():
            errors['last_name'].append('Pls enter alphabet')
        # Check the number of character
        if len(lastname) < 2:
            errors['last_name'].append('Last name can not be shorter than 2 characters')

        # Check the length of the password
        if len(password) < 8:
            errors['password'].append('Password is too short!')

        # Check the format of the email
        if len(email) != 0:
            regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
            if not (re.search(regex, email)):
                errors['email'].append('You must enter an valid email format')

        return errors


class User(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, default=None)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserManager()


class Person(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def num_photos(self):
        try:
            base_dir = "app/facerec/dataset"
            user_dir = os.path.join(base_dir, str(self.user_id.id))
            person_dir = os.path.join(user_dir, str(self.name))

            img_count = len(os.listdir(person_dir))
            print("number of photo")
            return img_count
        except:
            return 0


class Detected(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    person_id = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    person_name = models.CharField(max_length=255, null=True)
    time_stamp = models.DateTimeField()
    photo = models.ImageField(upload_to='detected/', default='app/facerec/detected/noimg.png')

    def __str__(self):
        if self.person_id is None:
            return f"{self.time_stamp}"
        else:
            person = Person.objects.get(name=self.person_id)
            return f"{person.name} {self.time_stamp}"

    def get_record(self):
        if self.person_id is None:
            person = Person.objects.get(name=self.person_id)
            return f"{person.name} {self.time_stamp}"
        else:
            return f"{self.time_stamp}"

