from django.test import TestCase
from webapp.models import Users, Invoices, Statements
# Create your tests here.


class RequestsClient:
    pass


class Test_Signup(TestCase):
    def setUp(self):
        Users.objects.create_user(username="123", password="test1", first_name="test1", last_name="test1")
        Users.objects.create_user(username="456", password="test2", first_name="test2", last_name="test2")
        self.client = RequestsClient()

    def normal_signup(self):
        response = self.client.post("127.0.0.1:8000/signup/",
                                    {"password": "test1",
                                     "first_name": "test1",
                                     "last_name": "test1"})
        self.assertEqual(response.status_code, 200)

    def signup_incomplete(self):
        response_1 = self.client.post("127.0.0.1:8000/signup/",
                                    {"first_name": "test1",
                                     "last_name": "test1"})

        response_2 = self.client.post("127.0.0.1:8000/signup/",
                                    {"password": "test1",
                                     "last_name": "test1"})
        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_2.status_code, 200)




class Test_Signin(TestCase):
    def setUp(self):
        Users.objects.create_user(username="123", password="test1", first_name="test1", last_name="test1")
        Users.objects.create_user(username="456", password="test2", first_name="test2", last_name="test2")
        self.client = RequestsClient()

    def normal_signin(self):
        response = self.client.post("127.0.0.1:8000/signup/",
                                    {"account_number": "123",
                                     "pwd": "test1"})
        self.assertEqual(response.status_code, 200)

