#! -*- coding: utf-8 -*-

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
The main BOT class.
"""

import logging
import re
import time
from . import ZoneMinder

from slackclient import SlackClient

LOGGER = logging.getLogger("zonebot")


class ZoneBot(object):
    """
    A smart bot that interacts with Slack via chat commands.
    """

    dispatch_map = dict(
        unknown=dict(
            function='unknown_command',
            name='unknown',
            permissions='any'
        ),
        help=dict(
            function='list_commands',
            name='help',
            permissions='any'
        ),
        denied=dict(
            function="command_denied",
            name='denied',
            permissions='any',
        ),
        commands=dict(
            function='list_commands',
            name='commands',
            help='List available commands',
            permissions='any'
        ),
        enable=dict(
            function='enable_monitor',
            name='enable',
            help='Enables alarms on the named monitor (by name, not monitor ID)',
            permissions='write'
        ),
        disable=dict(
            function='disable_monitor',
            name='disable',
            help='Disables alarms on the named monitor (by name, not monitor ID)',
            permissions='write'
        )
    )

    def __init__(self, config):
        self.config = config

        # Initialize class state
        self.last_ping = 0
        self.slack_client = SlackClient(config['Slack']['api_token'])

        self.AT_BOT = "<@" + config['Slack']['bot_id'] + ">"
        self.BOT_NAME = config['Slack']['bot_name'] or "zonebot"

        self._usermap = {}

    def start(self):
        """
        If configured, converts to a daemon. Otherwise start connected to the current console.
        """

        run_as_daemon = self.config.getboolean('Runtime', 'daemon', fallback=False)
        uid = self.config.get('Runtime', 'uid', fallback=None)
        gid = self.config.get('Runtime', 'gid', fallback=None)

        if run_as_daemon:
            LOGGER.info('Start as a daemon process')
            import daemon
            with daemon.DaemonContext(uid=uid, gid=gid):
                self._start()

        self._start()

    def _start(self):
        """
        Starts the bot by connecting to Slack.
        """
        self.zoneminder = ZoneMinder(self.config.get('ZoneMinder', 'url'))
        self.zoneminder.login(self.config.get('ZoneMinder', 'username'),
                              self.config.get('ZoneMinder', 'password'))

        self.connect()

        READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose

        while True:
            for reply in self.slack_client.rtm_read():
                user, channel, command = self._extract_command(reply, self.AT_BOT)
                if user and channel and command:
                    self.handle_command(user, command, channel)

            self.autoping()
            time.sleep(READ_WEBSOCKET_DELAY)

    def connect(self):
        """Convenience method that creates Server instance"""
        self.slack_client.rtm_connect()

    def autoping(self):
        """Pings the remote system to keep the connection alive"""
        # hardcode the interval to 3 seconds
        now = int(time.time())
        if now > self.last_ping + 60:
            self.slack_client.server.ping()
            self.last_ping = now

    @staticmethod
    def _extract_command(slack_data, bot_id):
        """

        The Slack Real Time Messaging API is an events firehose. this parsing function
        returns None unless a message is directed at the Bot, based on its ID.

        Extracts the channel, user and command from the slack data. If the data does
        not contain a command for the bot, then "None, None, None" is returned.

        :param slack_data: The data to check
        :type slack_data: dict
        :param bot_id: ID of the bot, looks like "<@AABB1122CC>"
        :type bot_id: str
        :return: user, channel, and command
        """

        if slack_data and len(slack_data) > 0:
            if 'text' in slack_data:
                # It looks like a chat message ..
                if bot_id in slack_data['text']:

                    # .. and it's for us.
                    # return text after the @ mention, whitespace removed
                    return slack_data['user'], \
                           slack_data['channel'], \
                           slack_data['text'].split(bot_id)[1].strip().lower()

        # No match ...
        return None, None, None

    def handle_command(self, user, command_string, channel):
        """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.

        :param user: user ID that issued the command
        :type user: str
        :param command_string: The command the user entered
        :type command_string: str
        :param channel: The channel the user sent the command in
        :type channel: str
        """

        LOGGER.info("Received command '%s' in channel %s from %s (%s)",
                    command_string,
                    channel,
                    user,
                    'name not cached' if user not in self._usermap else self._usermap[user])

        if not command_string:
            command = 'help'
            words = ['help']
        else:
            words = re.split('\W+', command_string)
            if len(words) == 0:
                command = 'unknown'
            else:
                command = words[0].lower()

        if not command or command not in self.dispatch_map:
            command = 'unknown'

        if not self._has_permission(user, command):
            command = 'denied'

        # pass of the command the the correct dispatch function
        function = self.dispatch_map[command]['function']
        response = getattr(self, function)(words, user)

        result = self.slack_client.api_call("chat.postMessage",
                                            channel=channel,
                                            text=response,
                                            as_user=True)

        if not result['ok']:
            error = "Error: "
            if 'error' in result:
                error = result['error']
            elif 'warning' in result:
                error = result['warning']

            LOGGER.error("Could not respond to the command: %s", error)

    def unknown_command(self, words, user):
        """
        Triggered for unknown commands.
        """

        return 'Unknown command {}. Use "@{} commands" to list available commands' \
            .format('' if len(words[0]) == 0 else words[0],
                    self.BOT_NAME)

    def command_denied(self, words, user):
        return "User does not have permission to execute the {} command".format(words[1])

    def list_commands(self, words, user):
        """
        Returns the commands allow for this bot (and user?)
        """

        result = 'Available commands:\n'

        for c in self.dispatch_map:
            if c in ['help', 'unknown', 'denied']:
                continue
            elif not self._has_permission(user, c):
                continue

            result += ' _{}_: {}\n'.format(self.dispatch_map[c]['name'], self.dispatch_map[c]['help'])

        return result

    def enable_monitor(self, words, user):
        """
        Enables alarms on the named monitor.
        """

        return self.__toggle_monitor(True, words, user)

    def disable_monitor(self, words, user):
        """
        Disables alarms on the named monitor.
        """

        return self.__toggle_monitor(False, words, user)

    def __toggle_monitor(self, on, words, user):
        """
        Toggles the active alarm state for the named monitor
        """

        if not words or len(words) < 2:
            return '*Error* the name of the monitor is required'

        return 'Monitor {} {}'.format(words[1], 'enabled' if on else 'disabled')

    def _has_permission(self, user_id, command):
        """
        Checks to see if the user has the required permissions to execute the provided
        command.
        :param user_id: Slack user ID of the user (e.g. 'U1234567890')
        :param command: The command to be checked
        :return: True if the user is allow the execute the command and false if they are not.
        :rtype: bool
        """

        if command not in self.dispatch_map:
            return False

        command_data = self.dispatch_map[command]

        if command_data['permissions'] == 'any':
            return True

        permission_required = command_data['permissions']

        # Now things get complicated.

        # First check to see if any permissions are defined. If they are not, then
        # anyone can do anything.
        if not self.config.has_section('Permissions'):
            LOGGER.info("No config section")
            return True

        # Well then. Let's turn the ID into a user name and see what their permissions are.
        # Results are cached so check the cache first

        user_name = None
        if user_id in self._usermap:
            user_name = self._usermap[user_id]

        if not user_name:
            LOGGER.info("Doing Slack lookup for user ID %s", user_id)
            result = self.slack_client.api_call("users.info",
                                                user=user_id,
                                                as_user=True)

            if not result['ok']:
                LOGGER.error("Could not convert %s to a user name: %s", user_id, result['error'])
                return False

            user_name = result['user']['name'].lower()
            self._usermap[user_id] = user_name

        if not user_name:
            LOGGER.error('Could not resolve user ID %s', user_id)
            return False

        # Not listed in the permissions section, they only have read access
        access = self.config.get('Permissions', user_name.lower(), fallback='read')
        access = access.split(' ')

        # They have specific permissions listed. See if this command is one of them

        if 'any' in access:
            # they are allowed to do anything
            return True
        if permission_required in access:
            # check by type
            return True
        elif command in access:
            # check by specific command
            return True

        # No match, not allowed
        LOGGER.info("User ID %s maps to %s and has access %s. They are not allowed the %s command",
                    user_id,
                    user_name,
                    access,
                    command)
        return False
