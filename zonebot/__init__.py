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
A Slack bot that can communicate and interact with a ZoneMinder security system.
"""

import sys
import os
import logging
import argparse
from configparser import ConfigParser
from .zoneminder import ZoneMinder
from slackclient import SlackClient

__version__ = '1.0'
__author__ = 'Robert Clark <clark@exiter.com>'

LOGGER = logging.getLogger("zonebot")


def __splitall(path):
    """
    Splits an OS path into all its component elements

    :param path: The absolute or relative path to be split
    :type path: str

    :return: An array containing all the elements of the path.
    """
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])

    # Strip a trailing blank, if there is one
    if len(allparts) > 0 and allparts[-1] == '':
        del allparts[-1]

    return allparts


def _init_logging(config):
    """
    Sets up the logging for the project. This will be to one of (in order)

      * a log file is specified in the config
      * syslog is running as a deamon
      * the console otherwise

    :param config: The configuration for the bot.

    """

    # TODO: check config.Logging for how we're supposed to log stuff.

    # Basic default console logger for now
    logging.basicConfig(
        format='[%(asctime)s][%(levelname)-5s] %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S %p',
        level=logging.INFO
    )


def _find_config(command_line_value=None):
    """
    Find the config file, search in all well known locations, in order

    :return: the config file to use. A exception is raised if no config file is found
    :rtype: str
    """

    # Locations are checked in order

    # Passed in value
    locations = [command_line_value]

    # XDG default directory
    if 'XDG_CONFIG_HOME' in os.environ:
        locations.append(os.path.join(os.environ['XDG_CONFIG_HOME'], 'zonebot', 'zonebot.conf'))

    # each of XDG_CONFIG_DIRS
    if 'XDG_CONFIG_DIRS' in os.environ:
        for location in os.environ['XDG_CONFIG_DIRS'].split(':'):
            locations.append(os.path.join(location, 'zonebot', 'zonebot.conf'))

    # user's config directory, may duplicate XDG_CONFIG_HOME
    locations.append(os.path.join(os.path.expanduser("~"), '.config', 'zonebot', 'zonebot.conf'))

    # System config directory
    locations.append('/etc/zonebot/zonebot.conf')

    # Debian directory config directory
    locations.append('/etc/default/zonebot')

    for location in locations:
        if location and os.path.isfile(location):
            return location

    raise ValueError("No config file was provided and none could be located.")


def _validate_config(config):
    """
    Make sure all the items necessary are available in the config object.

    :param config: The config object to check

    :returns: true if the config is value and false (with errors logged) otherwise
    """

    if not config:
        LOGGER.error("No config at all provided")
        return False

    # These are all the sections and options we require. If any are missing,
    # the bot will not start up.
    required = {
        "Slack": ["api_token", "bot_id"],
        "ZoneMinder": ["url", "username", "password"]
    }

    result = True

    for section in required:
        if not config.has_section(section):
            LOGGER.error("No [%s] section in the configuration", section)
            result = False
        else:
            for option in required[section]:
                if not config.has_option(section, option):
                    LOGGER.error("Required option %s missing from section [%s]", option, section)
                    result = False

    # Finally
    return result

def zonebot_getid_main():
    """
    Main method for the util script that figures out the bot ID
    """

    #  Set up the command line arguments we support
    parser = argparse.ArgumentParser(description='Find the ID for a Slack bot user',
                                     epilog="Version " + __version__ + " (c) " + __author__)

    parser.add_argument('-a', '--apitoken',
                        metavar='key',
                        required=True,
                        help='Slack API token')

    parser.add_argument('-b', '--botname',
                        metavar='name',
                        required=True,
                        help='Name of the Slack bot user to search for')

    args = parser.parse_args()

    slack_client = SlackClient(args.apitoken)
    api_call = slack_client.api_call("users.list")

    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name').lower() == args.botname.lower():
                print("User ID for bot '{0}' is {1}".format(user['name'], user.get('id')))
                sys.exit(0)
    else:
        print("Slack API call failed (invalid API token?")

    # Not found
    print("Could not find bot user with the name {0}".format(args.botname))
    sys.exit(1)


def zonebot_main():
    """
    Main method for the zonebot script
    """

    #  Set up the command line arguments we support
    parser = argparse.ArgumentParser(description='A Slack bot to interact with ZoneMinder',
                                     epilog="Version " + __version__ + " (c) " + __author__)

    parser.add_argument('-c', '--config',
                        metavar='file',
                        required=False,
                        help='Load the specified config file')

    args = parser.parse_args()

    # Create the configuration from the arguments
    config = ConfigParser()
    config_file = _find_config(args.config)
    if config_file:
        config.read(config_file)
    else:
        LOGGER.error("No config file could be located")
        sys.exit(1)

    _init_logging(config)

    LOGGER.info("Starting up")
    LOGGER.info("Version %s", __version__)

    if not _validate_config(config):
        sys.exit(1)

    LOGGER.info("Configuration is valid")


def zonebot_alert_main():
    """
    Main method for the zonebot-alert script
    """

    #  Set up the command line arguments we support
    parser = argparse.ArgumentParser(
        description='A script that receives event notifications from ZoneMinder',
        epilog="Version " + __version__ + " (c) " + __author__)

    parser.add_argument('event_dir',
                        help='The directory in which the event files are stored')

    parser.add_argument('-c', '--config',
                        metavar='file',
                        required=False,
                        help='Load the specified config file')

    args = parser.parse_args()

    # Create the configuration from the arguments
    config = ConfigParser()
    config_file = _find_config(args.config)
    if config_file:
        config.read(config_file)
    else:
        LOGGER.error("No config file could be located")
        sys.exit(1)

    _init_logging(config)

    if not _validate_config(config):
        sys.exit(1)

    elements = __splitall(args.event_dir)

    # Array will contain a variable number of leading elements
    # but always ends with:
    #   monitor/yy/mm/d/hh/mm/ss
    # we split that to
    #   monitor id
    # and
    #   yyyy-mm-dd hh:mm:ss

    idx = -7
    if elements[-1] == '':
        # Just in case the path ends with a '/'
        idx = -8

    monitor = elements[idx]
    timestamp = "20" + elements[idx+1] + "-" + elements[idx+2] + "-" + elements[idx+3] + " " + \
                elements[idx+4] + ":" + elements[idx+5] + ":" + elements[idx+6]

    LOGGER.info("Sending alert about event at %s on monitor %s", timestamp, monitor)

    zone_minder = ZoneMinder(config.get('ZoneMinder', 'url'),
                             config.get('ZoneMinder', 'username'),
                             config.get('ZoneMinder', 'password'))

    data = zone_minder.load_event(monitor, timestamp)
    data = zone_minder.parse_event(data)

    # see if we have a message to load
    if 'key_frame' in data:
        data['image'] = zone_minder.load_image(data['key_frame'])

