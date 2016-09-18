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
All the commands possible for the bot. This is basically a big routing table.
"""

import logging
from abc import ABCMeta, abstractmethod

LOGGER = logging.getLogger("zonebot")


class Command(metaclass=ABCMeta):

    """ Static mapping of Slack user IDs to user names """
    _usermap = {}

    def __init__(self, config=None):
        self.config = config

    @abstractmethod
    def perform(self, user_name, commands, zoneminder):
        pass

    @abstractmethod
    def report(self, slack, channel):
        pass

    @staticmethod
    def log_slack_result(result):
        """
        Logs the result of a slack API call.

        :param result: The result object from Slack
        """

        if not result:
            return

        if not result['ok']:
            error = "Error: "
            if 'error' in result:
                error = result['error']
            elif 'warning' in result:
                error = result['warning']

            LOGGER.error("Could not respond to the command: %s", error)

    @staticmethod
    def resolve_user(user_id, slack):
        """
        Resolve (if not already cached) the Slack user ID into a user name

        :param user_id: Slack user ID of the user (e.g. 'U1234567890')
        :type user_id: str
        :param slack: A fully configured `slackclient` instance
        :return: The resolved name of the user or `None` if the user ID could not be resolved.
        """

        if not user_id:
            return None

        user_name = None
        if user_id in Command._usermap:
            user_name = Command._usermap[user_id]

        if not user_name:
            LOGGER.info("Doing Slack lookup for user ID %s", user_id)
            result = slack.api_call("users.info",
                                    user=user_id,
                                    as_user=True)

            if result['ok']:
                user_name = result['user']['name'].lower()
                Command._usermap[user_id] = user_name
            else:
                LOGGER.error("Could not convert %s to a user name: %s", user_id, result['error'])

        return user_name

    @staticmethod
    def has_permission(user_name, config, command, permission):
        """
        Checks to see if the user has the required permissions to execute the provided
        command.

        :param user_name: Name of the user (*not* the Slack user ID)
        :type user_name: str
        :param permission:
        :param command:
        :param config:
        :return: True if the user is allow the execute the command and false if they are not.
        :rtype: bool
        """

        if 'any' == permission:
            return True

        # Now things get complicated.

        # First check to see if any permissions are defined. If they are not, then
        # anyone can do anything.
        if not config or not config.has_section('Permissions'):
            LOGGER.info("No config section")
            return True

        if not user_name:
            LOGGER.error('Could not resolve user ID %s', user_name)
            return False

        # Not listed in the permissions section, they only have read access
        access = config.get('Permissions', user_name.lower(), fallback='read')
        access = [x.strip() for x in access.split(',')]

        # They have specific permissions listed. See if this command is one of them

        if 'any' in access:
            # they are allowed to do anything
            return True
        if permission in access:
            # check by type
            return True
        elif command in access:
            # check by specific command
            return True

        # No match, not allowed
        LOGGER.info("User name %s and has access %s. They are not allowed the %s command",
                    user_name,
                    access,
                    command)

        return False


class Help(Command):
    def __init__(self, config=None):
        super(Help, self).__init__(config=config)

    def perform(self, user_name, commands, zoneminder):
        pass

    def report(self, slack, channel):
        return slack.api_call("chat.postMessage",
                              channel=channel,
                              text='Help command detected',
                              as_user=True)


class Unknown(Command):
    def __init__(self, config=None):
        super(Unknown, self).__init__(config=config)

    def perform(self, user_name, commands, zoneminder):
        pass

    def report(self, slack, channel):
        return slack.api_call("chat.postMessage",
                              channel=channel,
                              text='Unknown command detected',
                              as_user=True)


class Denied(Unknown):
    def __init__(self, config=None):
        super(Denied, self).__init__(config=config)

    def report(self, slack, channel):
        return slack.api_call("chat.postMessage",
                              channel=channel,
                              text='*Error* You don\'t have permission to execute this command',
                              as_user=True)


class ListMonitors(Command):
    def __init__(self, config=None):
        super(ListMonitors, self).__init__(config=config)

        self.attachments = []

    def perform(self, user_name, commands, zoneminder):
        monitors = zoneminder.get_monitors()
        monitors.load()

        for monitor_name in monitors.monitors:
            monitor = monitors.monitors[monitor_name]

            enabled = 'Yes' if monitor['Enabled'] == '1' else 'No'
            color = '#2fa44f' if monitor['Enabled'] == '1' else '#d52000'

            self.attachments.append({
                'text': '{0} (ID: {1})'.format(monitor['Name'], monitor['Id']),
                'fields': [
                    {
                        'title': 'Enabled',
                        'value': enabled,
                        'short': True
                    },
                    {
                        'title': 'Detection',
                        'value': monitor['Function'],
                        'short': True
                    }
                ],
                'color': color
            })

    def report(self, slack, channel):
        return slack.api_call("chat.postMessage",
                              channel=channel,
                              attachments=self.attachments,
                              as_user=True)


class ToggleMonitor(Command):
    def __init__(self, config=None):
        super(ToggleMonitor, self).__init__(config=config)

    def perform(self, user_name, commands, zoneminder):
        pass

    def report(self, slack, channel):
        return slack.api_call("chat.postMessage",
                              channel=channel,
                              text='toggle monitor detected',
                              as_user=True)

__all_commands = {
    'unknown': {
        'permission': 'any',
        'classname': Unknown
    },
    'help': {
        'permission': 'any',
        'classname': Help
    },
    'denied': {
        'permission': 'any',
        'classname': Denied
    },
    'list monitors': {
        'permission': 'read',
        'help': 'List all monitors and their current state',
        'classname': ListMonitors
    },
    'enable monitor': {
        'permission': 'write',
        'help': 'Enable alarms on a monitor (supplied by name, not ID)',
        'classname': ToggleMonitor
    },
    'disable monitor': {
        'permission': 'write',
        'help': 'Disable alarms on a monitor (supplied by name, not ID)',
        'classname': ToggleMonitor
    }
}


def get_command(words, user_id=None, config=None, slack=None):
    if not words or len(words) < 1:
        return Help()

    command_text = words[0].strip().lower()
    if command_text not in __all_commands:
        if len(words) > 1:
            command_text = '{0} {1}'.format(words[0].strip().lower(), words[1].strip().lower())

    if command_text not in __all_commands:
        return Unknown()

    perms = __all_commands[command_text]['permission']
    user_name = Command.resolve_user(user_id, slack)

    if not Command.has_permission(user_name, config, command_text, perms):
        return Denied()

    return __all_commands[command_text]['classname'](config=config)

