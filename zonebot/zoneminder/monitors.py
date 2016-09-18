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
The monitors attached to a ZoneMinder system
"""

import json
import logging

LOGGER = logging.getLogger("zoneminder")


class Monitors(object):
    """
    Manages the monitors associated with a ZoneMinder system. This assumes that a session
    has already been created and a login successfully completed.
    """

    def __init__(self, session, url):
        """
        Initializes the list of monitors.

        :param session: The session (from `requests`) that will be used to communicate
        :type session: requests.session
        :param url: base URL for the ZoneMinder system
        :type url: str
        """

        self.session = session
        self.url = url
        self.monitors = {}

    def load(self):
        """
        Loads (or reloads) the list of monitors attached to ZoneMinder
        """

        url = '{0}/api/monitors.json'.format(self.url)

        monitor_data = self.session.get(url=url)
        if monitor_data.status_code != 200:
            raise Exception("Could not obtain list of monitors. " +
                            "Response code " + str(monitor_data.status_code))

        monitor_list = json.loads(monitor_data.text)
        if 'monitors' not in monitor_list:
            raise Exception("Could not obtain list of monitors. Unknown error")

        self.monitors = {}

        for monitor in monitor_list['monitors']:
            m = monitor['Monitor']
            self.monitors[m['Name'].lower()] = m

    def get_value(self, monitor_name, value_name):
        """
        Returns the named value from the named monitor. Assumes `load` has already been called.

        :param monitor_name: The name (not ID) of the monitor
        :param value_name: The value to get from the monitor
        :return: The named value or None
        :rtype: str
        """

        monitor = self.__get_monitor(monitor_name)
        if not monitor:
            return None

        return monitor[value_name]

    def is_enabled(self, monitor_name):
        """
        Whether or not the named monitor is both attached and enabled. Assumes `load`
        has already been called.

        :param monitor_name: The name of the monitor to look for (case-insensitive)
        :type monitor_name: str
        :return: True if the monitor is present and enabled and false if it is not.
        :rtype: bool
        """

        return '1' == self.get_value(monitor_name, 'Enabled')

    def set_state(self, monitor_name, state):
        """
        Enables or disabled the monitor with the provided name
        :param monitor_name: The name of the monitor to look for (case-insensitive)
        :type monitor_name: str
        :param state: True if enabled, False if disabled
        :type state: bool
        :return: Message describing the status of the operation
        """

        # Load to get the initial state and list
        self.load()

        monitor = self.__get_monitor(monitor_name)
        if not monitor:
            return 'not found'

        url = '{0}/api/monitors/{1}.json'.format(self.url, monitor['Id'])

        params = {
            'Monitor[Enabled]': '1' if state else '0'
        }

        result = self.session.post(url=url, data=params)
        if result.status_code != 200:
            return "not changed. Response code " + str(result.status_code)

        result = json.loads(result.text)
        if result['message'] != 'Saved':
            return "not changed: {0}".format(result['Message'])

        # Reload to get the new monitor state
        self.load()
        enabled = self.get_value(monitor_name, 'Enabled')
        if enabled is None:
            return 'no longer available'

        return 'changed to ' + ('enabled' if enabled == '1' else 'disabled')

    def __get_monitor(self, monitor_name):
        """
        Gets the monitor with the provided name.

        :param monitor_name: The name of the monitor to look for (case-insensitive)
        :type monitor_name: str
        :return: The named monitor `json` object or None if the monitor was not found
        """

        if not monitor_name:
            return None

        name = monitor_name.lower()

        if name not in self.monitors:
            return None

        return self.monitors[name]
