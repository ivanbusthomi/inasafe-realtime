# coding=utf-8
import logging

from hammock import Hammock

from realtime import settings
from realtime.utilities import realtime_logger_name

__author__ = 'Rizky Maulana Nugraha <lana.pcfre@gmail.com>'
__date__ = '12/1/15'

LOGGER = logging.getLogger(realtime_logger_name())


class InaSAFEDjangoREST(object):

    def __init__(self):
        self.base_rest = Hammock(
            settings.INASAFE_REALTIME_REST_URL, append_slash=True)
        self.session_login()

    def base_url(self):
        return str(self.base_rest)

    def session_login(self):
        """Session login to Realtime InaSAFE Django
        """
        r = self.base_rest.auth.login.GET()
        csrf_token = r.cookies.get('csrftoken')
        login_data = {
            'username': settings.INASAFE_REALTIME_REST_USER,
            'password': settings.INASAFE_REALTIME_REST_PASSWORD,
            'csrfmiddlewaretoken': csrf_token,
            'next': settings.INASAFE_REALTIME_REST_URL
        }
        self.base_rest.auth.login.POST(data=login_data)

    @property
    def rest(self):
        return self.base_rest

    @classmethod
    def is_configured(cls):
        """Determine if realtime REST is configured.

        :return: True if Realtime REST credentials is provided in os.environ
        """
        return (settings.INASAFE_REALTIME_REST_URL and
                settings.INASAFE_REALTIME_REST_USER and
                settings.INASAFE_REALTIME_REST_PASSWORD)

    @property
    def cookies(self):
        r = self.base_rest.auth.login.GET()
        return r.cookies

    @property
    def csrf_token(self):
        return self.cookies.get('csrftoken')

    @property
    def is_logged_in(self):
        headers = {
            'X-CSRFTOKEN': self.csrf_token
        }
        r = self.base_rest.is_logged_in.GET(headers=headers)
        return r.json().get('is_logged_in')
