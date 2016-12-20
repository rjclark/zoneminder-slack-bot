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
import os
from pwd import getpwnam
from grp import getgrnam

from slackclient import SlackClient
from zonebot.zoneminder.zoneminder import ZoneMinder
import zonebot.commands

LOGGER = logging.getLogger("zonebot")


class ZoneBot(object):
    """
    A smart bot that interacts with Slack via chat commands.
    """

    def __init__(self, config):
        self.config = config

        # Initialize class state
        self.last_ping = 0
        self.slack_client = SlackClient(config['Slack']['api_token'])

        self.at_bot = "<@" + config['Slack']['bot_id'] + ">"
        self.bot_name = config['Slack']['bot_name'] or "zonebot"

    def start(self):
        """
        If configured, converts to a daemon. Otherwise start connected to the current console.
        """

        run_as_daemon = self.config.getboolean('Runtime', 'daemon', fallback=False)
        uid = self.config.get('Runtime', 'daemon user', fallback=None)
        gid = self.config.get('Runtime', 'daemon group', fallback=None)
        pidfile = self.config.get('Runtime', 'daemon pid file', fallback=None)

        if uid:
            uid = getpwnam(uid).pw_uid
        if gid:
            gid = getgrnam(gid).gr_gid

        if run_as_daemon:
            LOGGER.info('Starting as a daemon process')
            import daemon
            import daemon.pidfile

            if pidfile:
                # We need to create the enclosing directory (if it does not exist) before
                # starting the daemon context as we might lose the permissions to create
                # that directory
                piddir = os.path.dirname(pidfile)
                if not os.path.isdir(piddir):
                    os.makedirs(piddir, 0o0755)
                    os.chown(piddir, uid, gid)

                # Convert the filename to the appropriate type for the deamon module.
                pidfile = daemon.pidfile.TimeoutPIDLockFile(pidfile)

            with daemon.DaemonContext(uid=uid, gid=gid, pidfile=pidfile):
                self._start()

        self._start()

    def _start(self):
        """
        Starts the bot by connecting to Slack.
        """

        self.zoneminder = ZoneMinder(self.config)
        self.zoneminder.login()

        while True:
            try:
                self.__polling_loop()
            except KeyboardInterrupt:
                return
            except (TimeoutError, ConnectionResetError) as e:
                LOGGER.warning("Connection to Slack lost, reconnecting: %s", str(e))
                time.sleep(30)
            except Exception as e:
                LOGGER.exception("Unhandled exception, terminating process: %s", str(e))
                return

    def __polling_loop(self):
        """Polling loop, without re-connect logic"""

        read_websocket_delay = 1  # 1 second delay between reading from firehose

        self.connect()

        while True:
            for reply in self.slack_client.rtm_read():
                user, channel, command = self._extract_command(reply, self.at_bot)
                if user and channel and command:
                    self.handle_command(user, command, channel)

            self.autoping()
            time.sleep(read_websocket_delay)

    def connect(self):
        """Convenience method that creates Server instance"""

        self.slack_client.rtm_connect()

    def autoping(self):
        """Pings the remote system to keep the connection alive"""

        # hardcode the interval to 60 seconds
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
                           slack_data['text'].split(bot_id)[1].strip()

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

        user_name = zonebot.commands.Command.resolve_user(user, self.slack_client)

        LOGGER.info("Received command '%s' in channel %s from %s",
                    command_string,
                    channel,
                    user_name if user_name else user)

        if not command_string:
            words = ['help']
        else:
            words = re.split(r'\W+', command_string)

        # Remove any blank or empty entries
        words = [x for x in words if x]

        start_time = time.time()

        cmd = zonebot.commands.get_command(words, user_name=user_name, config=self.config)
        cmd.perform(user_name=user_name, commands=words, zoneminder=self.zoneminder)
        result = cmd.report(self.slack_client, user_name, channel)

        duration = time.time() - start_time
        LOGGER.debug("Completed command '%s' in %f seconds", command_string, duration)

        zonebot.commands.Command.log_slack_result(result)

