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
import logging
from io import BytesIO

LOGGER = logging.getLogger("zoneminder")


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

        while url.endswith("/"):
            # We need the URL in a consistent format as some of the API calls
            # fail if there are too many slashes. I decided on no trailing slash
            #  as the default format
            url = url[:-1]

        self.url = url
        LOGGER.debug("Base url is %s" % self.url)

        params = {
            "username": username,
            "password": password,
            "action": "login",
            "view": "console"
        }

        # If successful, a cookie will be added to the session  (called ZMSESSID)
        # which we can use for a limited time to provide to the server that we have
        # already logged in.
        login_request = self.session.post(self.url + '/', data=params)

        if login_request.status_code != 200:
            raise Exception("Could not log into %s response code %d" %
                            (self.url, login_request.status_code))

    def load_event(self, monitor, timestamp):
        """
        Queries the server for the event with the provided starting timestamp and monitor

        :param monitor: The monitor from the which the event was generated
        :type monitor: str
        :param timestamp: The timestamp ('yyyy-mm-dd hh:mm:ss') at which the event started
        :type timestamp: str
        :return: A JSON object containing the loaded event
        """

        url = "{0}/api/events/index/MonitorId:{1}/StartTime =:{2}.json".format(
            self.url,
            monitor,
            timestamp)

        LOGGER.debug("Loading event metadata from %s" % url)

        timestamp_request = self.session.get(url=url)
        if timestamp_request.status_code != 200:
            raise Exception("Could not obtain data for timestamp " +
                            timestamp + " response code " + str(timestamp_request.status_code))

        # This should be the list of events that match our query. Hopefully only on, but
        # we only ever refer to the first item.
        data = json.loads(timestamp_request.text)

        # Now we should have the event ID in the returned data.
        event_id = data['events'][0]["Event"]["Id"]

        # Make a query for just this ID
        url = "{0}/api/events/{1}.json".format(self.url, event_id)
        LOGGER.debug("Loading event from %s" % url)

        event_request = self.session.get(url=url)
        if event_request.status_code != 200:
            raise Exception("Could not obtain data for event " +
                            event_id + " response code " + str(event_request.status_code))

        data = json.loads(event_request.text)
        return data

    @staticmethod
    def parse_event(data):
        """
        Parses the provided event data to extract a dictionary with:

         * 'source' - name of the monitor
         * 'event' - name of the event
         * 'cause' - what caused the event ("Modetect" for motion detection, etc)
         * 'duration' - event length, in seconds
         * 'id' - Number ID of the event
         * 'key_frame' - index number of the image in the event with the highest score.

        :param data: the JSON data representing the event
        :type data: dict
        :return: a dictionary with the parsed event data.
        :rtype: dict
        """

        result = {
                  'source': data['event']['Monitor']['Name'],
                  'event': data['event']['Event']['Name'],
                  'cause': data['event']['Event']['Cause'],
                  'duration': data['event']['Event']['Length'],
                  'id': data['event']['Event']['Id']
                  }

        score = 0
        key_frame = None

        for frame in data['event']['Frame']:
            if int(frame['Score']) > score:
                key_frame = frame['Id']
                score = int(frame['Score'])

        result['key_frame'] = key_frame

        return result

    def load_image(self, key_frame):
        """
        Loads the image with the specified ID into memory.

        :param key_frame: The index of the image that is to be loaded (e.g "12345").
        :type key_frame: str
        :return: The in-memory representation of the image.
        :rtype: io.BytesIO
        """

        # Load key frame image from http://<site>/zm/index.php?view=image&fid=<frame id>
        url = "{0}/index.php".format(self.url)

        LOGGER.debug("Loading image ID %s from %s", key_frame, url)

        params = {
            "view": "image",
            "fid": key_frame
        }

        image_request = self.session.get(url, params=params)
        image = BytesIO(image_request.content)

        return image