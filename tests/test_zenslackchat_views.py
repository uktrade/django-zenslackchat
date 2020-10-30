import json
import datetime
from unittest.mock import patch

from django.test import RequestFactory, TestCase
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

from zenslackchat import views


class WebAppAndAPITest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.api_factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='bob', 
            email='bob.sprocket@example.com', 
            password='Password1'
        )

    def test_anonymous_index_view_requires_auth(self):
        """Check that anonymous user requires login.
        """
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = views.index(request)
        # As there is no logged in user this should result in a redirect
        self.assertEqual(response.status_code, 302)
        # We should be redirected to the login page:
        self.assertEqual(response.url, '/accounts/login/?next=/')        

    def test_identified_user_on_index_view(self):
        """Check that anonymous user requires login.
        """
        request = self.factory.get('/')
        request.user = self.user
        response = views.index(request)

        # As there is a loggedd-in user this should not redirect:
        assert response.status_code == 200

        # Check the Pingdom ID is present to indicate successful login:
        content = response.content.decode()
        assert content.find('user_login_ok') != -1

    @patch('zenslackchat.views.messages')
    def test_trigger_daily_report_view(self, messages):
        """Check an authorised person can trigger the daily report.
        """
        # Check that anonymous user results in redirect to the login:
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = views.trigger_daily_report(request)
        assert response.status_code == 302
        self.assertEqual(response.url, '/accounts/login/?next=/')        
        messages.success.assert_not_called()

        # Now try with a logged-in user:
        request = self.factory.get('/')
        request.user = self.user
        response = views.trigger_daily_report(request)
        # We should be redirect back to root and the messages should have
        # been called.
        assert response.status_code == 302
        self.assertEqual(response.url, '/')        
        messages.success.assert_called()