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

import json
import logging
import time
import hashlib
from io import BytesIO

import requests
from zonebot.zoneminder.monitors import Monitors
from zonebot.zoneminder.session import Session

LOGGER = logging.getLogger("zoneminder")


class ZoneMinder(object):
    """
    Connect to an interact with a [ZoneMinder](https://www.zoneminder.com/) install.

    The associated HTTP session, and all actions, are not available until `login` is called.
    """

    # The default session timeout in ZoneMinder (specifically the Cake PHP library it
    # uses) is 120 seconds.
    __default_session_timeout = 100

    def __init__(self, config):
        """
        Creates a new class to interact with Zoneminder. Each class is a separate session.
        The user name and password are not stored. Instead we log into the Zoneminder
        system and store a cookie in the session that proves we have authorization.

        :param config: Bot configuration
        :type config: configparser.ConfigParser
        """

        url = config.get('ZoneMinder', 'url')

        while url.endswith("/"):
            # We need the URL in a consistent format as some of the API calls
            # fail if there are too many slashes. I decided on no trailing slash
            #  as the default format
            url = url[:-1]

        self.url = url
        LOGGER.debug("Base url is %s", self.url)

        self.config = config

        # Filled in when we login()
        self.session = None
        self.monitors = None

    def login(self):
        """
        Creates a new session by logging into the ZoneMinder system
        """

        self.session = Session(self.config.get('ZoneMinder', 'username', fallback=''),
                               self.config.get('ZoneMinder', 'password', fallback=''),
                               self.url,
                               self.__default_session_timeout)

        # extra classes for the various components of ZoneMinder
        self.monitors = Monitors(self.session, self.url)

    def get_status(self):
        """
        Obtains general status information about this install

        :return: daemon state, process load, disk used
        :rtype: dict
        """

        status = {}

        #
        # Version
        #
        url = "{0}/api/host/getVersion.json".format(self.url)
        response = self.session.get(url=url)
        if response.status_code != 200:
            status['version'] = 'Could not obtain ZoneMinder version. Response code {0}' \
                .format(response.status_code)
        else:
            data = json.loads(response.text)
            status['version'] = data['version']

        #
        # Daemon status
        #
        url = "{0}/api/host/daemonCheck.json".format(self.url)
        response = self.session.get(url=url)
        if response.status_code != 200:
            status['daemon'] = 'Could not obtain daemon status. Response code {0}'\
                .format(response.status_code)
        else:
            data = json.loads(response.text)
            status['daemon'] = 'Running' if 1 == data['result'] else '*Not Running*'

        #
        # Load average
        #
        url = "{0}/api/host/getLoad.json".format(self.url)
        response = self.session.get(url=url)
        if response.status_code != 200:
            status['load'] = 'Could not obtain process load status. Response code {0}' \
                .format(response.status_code)
        else:
            data = json.loads(response.text)
            status['load'] = '/'.join(map(str, data['load']))

        #
        # Disk usage. This very, ***VERY*** often times out and is currently disabled.
        #
        status['usage'] = []
        # url = "{0}/api/host/getDiskPercent.json".format(self.url)
        # response = self.session.get(url=url)
        # if response.status_code != 200:
        #     status['usage'] = 'Could not obtain disk usage status. Response code {0}' \
        #         .format(response.status_code)
        # else:
        #     data = json.loads(response.text)
        #     for u in data['usage']:
        #         if 'Total' == u:
        #             continue
        #         status['usage'].append({
        #             'name': u,
        #             'space': float(data['usage'][u]['space'])
        #         })

        return status

    def get_monitors(self):
        """
        Obtains the list of monitors connected to ZoneMinder. You must call `login` first.

        :return: the list of monitors currently connected.
        """

        return self.monitors

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

        LOGGER.debug("Loading event metadata from %s",  url)

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
        LOGGER.debug("Loading event from %s", url)

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
        key_frame_id = None

        for frame in data['event']['Frame']:
            if int(frame['Score']) > score:
                key_frame = frame['Id']
                key_frame_id = frame['FrameId']
                score = int(frame['Score'])

        result['key_frame'] = key_frame
        if key_frame_id:
            result['image_filename'] = key_frame_id.zfill(5) + '-capture.jpg'

        return result

    def get_still_image(self, monitor):
        """
        Returns a single still image from the monitor.

        :param monitor: The numeric monitor ID to retrieve the image from
        :type monitor: int
        :return:
        """

        zms = self.config.get('ZoneMinder', 'PATH_ZMS', fallback='')

        # Problem: url ends with '/zm/' (probably) and zms path starts with '/zm' (probably)
        # zms is defined as the full path from the host so we should be able to reconstruct
        # from the URL.

        # path, params, query, fragment ignored
        scheme, netloc = requests.utils.urlparse(self.url)[0:2]

        auth = _build_login_hash(self.config)

        url = '{0}://{1}{2}?mode=single&scale=100&monitor={3}{4}{5}'.format(
            scheme,
            netloc,
            zms,
            monitor,
            '' if not auth else '&',
            '' if not auth else auth
        )

        # http://server.example.com/zm/cgi-bin/nph-zms?mode=single&scale=100&monitor=1&auth=somerandomstring
        LOGGER.debug('Requesting image from %s', url)

        response = self.session.get(url, stream=True)
        if response.status_code != 200:
            return None, 'Could not download image. Response code {0}'.format(response.status_code)

        return BytesIO(response.content), None


def _build_login_hash(config):
    """
    Builds the hash necessary for logging in to the ZoneMinder server. This
    ensures that the user name and password are never transmitted over the wire.

    ..note:: Hashes are valid for up to two hours.

    See http://blog.chapus.net/zoneminder-hash-logins/

    :param config: Current configuration of the bot
    :type config: configparser.ConfigParser

    :returns: The time-limited, encoded, query string that we need to pass to ZoneMinder
    :rtype: str
    """

    use_auth = config.getboolean('ZoneMinder', 'OPT_USE_AUTH', fallback=True)
    if not use_auth:
        return None

    # These all have to be here or the login at startup would have failed out.
    username = config.get('ZoneMinder', 'username', fallback=None)
    password = config.get('ZoneMinder', 'password', fallback=None)

    auth_relay = config.get('ZoneMinder', 'AUTH_RELAY', fallback='plain')
    if 'plain' == auth_relay:
        return 'user={0}&pass={1}'.format(username, password)
    elif 'none' == auth_relay:
        return 'user={0}'.format(username)

    # We must need to generate an auth hash

    auth_hash_secret = config.get('ZoneMinder', 'AUTH_HASH_SECRET', fallback='')

    # Timestamp fields are:
    #   current hour (0-23)
    #   day of the month (1-31)
    #   month (PHP indexes from zero so subtract 1)
    #   year (PHP indexes from year 1900, so 2016 - 2000 + 100 == 116)
    timestamp = time.localtime()

    #
    # password needs to be hashed when ZM_AUTH_TYPE is 'hashed'
    # the hashing is done by the MySQL 'password()' function
    #
    password = __mysql_password_hash(password)

    auth_key = '{0}{1}{2}{3}{4}{5}{6}'.format(
        auth_hash_secret,
        username,
        password,
        str(timestamp[3]),
        str(timestamp[2]),
        str(timestamp[1] - 1),
        str(timestamp[0] - 2000 + 100)
    )

    hashcode = hashlib.md5()
    hashcode.update(auth_key.encode('utf-8'))

    return 'auth={0}'.format(hashcode.hexdigest())


def __mysql_password_hash(passwd):
    """
    Hash string twice with SHA1 and return uppercase hex digest,
    prepended with an asterisk.

    This function is identical to the MySQL PASSWORD() function.
    """
    pass1 = hashlib.sha1(passwd.encode('utf-8')).digest()
    pass2 = hashlib.sha1(pass1).hexdigest()
    return "*" + pass2.upper()
