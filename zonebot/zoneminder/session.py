#
# Copyright 2016 Robert Clark (clark@exiter.com)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

"""
Wraps a Python `requests.session` and imposes a timeout on it.
"""

import logging
import time
import requests

LOGGER = logging.getLogger("zoneminder")


class Session(object):
    """
    Make sure that we have a hard timeout on sessions and can force a re-login when needed.
    """

    def __init__(self, username, password, url, timeout=30*60):
        """

        :param username: User name to use when login in
        :param password:  Password to user (cached)
        :param url: Base URL for logins
        :param timeout: When a session times out and a login is force. Defaults to 30 minutes.
        """

        self.__username = username
        self.__password = password
        self.__url = url
        self.__timeout = timeout

        self.session = None
        self.last_login = 0

    def login(self):
        """
        Creates a new session by logging into the ZoneMinder system
        """

        LOGGER.info("Logging into %s", self.__url)

        self.session = requests.Session()

        params = {
            "username": self.__username,
            "password": self.__password,
            "action": "login",
            "view": "console"
        }

        # If successful, a cookie will be added to the session (called ZMSESSID)
        # which we can use for a limited time to provide to the server that we have
        # already logged in.
        login_request = self.session.post(self.__url + '/', data=params)

        if login_request.status_code != 200:
            raise Exception("Could not log into %s response code %d" %
                            (self.__url, login_request.status_code))

        self.last_login = time.time()

    def get(self, url, **kwargs):
        """Sends a GET request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        if self._login_expired():
            self.login()

        result = self.session.get(url, **kwargs)
        if result and result.status_code == 200:
            # We have refreshed the session.
            self.last_login = time.time()

        return result

    def post(self, url, data=None, json=None, **kwargs):
        """Sends a POST request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body
                     of the :class:`Request`.
        :param json: (optional) json to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        if self._login_expired():
            self.login()

        result = self.session.post(url, data, json, **kwargs)

        if result and result.status_code == 200:
            # We have refreshed the session.
            self.last_login = time.time()

        return result

    def _login_expired(self):
        """
        Checks to sees if this session is expired
        :return: `True` if the session is expired and false if it is not.
        """

        if self.last_login == 0 or self.last_login + self.__timeout < time.time():
            LOGGER.info("Session expired, forcing a re-login to ZoneMinder server")
            return True

        return False
