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
Class(es) to connect to and interact with a [ZoneMinder](https://www.zoneminder.com/) install.
"""

import requests
import json


class ZoneMinder(object):
    """
    Connect to an interact with a [ZoneMinder](https://www.zoneminder.com/) install.

    A session is created as soon as this class is, and a login is attempted immediately.
    """

    def __init__(self, url, username, password):
        """
        Creates a new class to interact with Zoneminder. Each class is a separate session.
        The user name and password are not stored. Instead we log into the Zoneminder
        system and store a cookie in the session that proves we have authorization.

        :param url: The URL of the Zoneminder installation.
        :type url: str
        :param username: The user name to use when connecting
        :type username: str
        :param password: The password to use when connecting
        :type password: str
        """

        self.session = requests.Session()

        if not url.endsWith("/"):
            # URL needs a trailing slash no matter what or we get a 301 redirect instead
            # of the required login prompt.
            url = url + "/"

        params = {
            "username": username,
            "password": password,
            "action": "login",
            "view": "console"
        }

        # If successful, a cookie will be added to the session  (called ZMSESSID)
        # which we can use for a limited time to provide to the server that we have
        # already logged in.
        login_request = self.session.post(url, data=params)

        if login_request.status_code != 200:
            raise Exception("Could not log into %s reponse code %d" %
                            (url, login_request.status_code))

    def load_event(self, monitor, timestamp):
        pass
