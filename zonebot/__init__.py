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

import logging
import os

from zonebot.bot import ZoneBot
from zonebot import commands, zonebot_get_id, zonebot_alert, zonebot_main

__version__ = '1.0'
__author__ = 'Robert Clark <clark@exiter.com>'

LOGGER = logging.getLogger("zonebot")


def split_os_path(path):
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


def init_logging(config=None):
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


def find_config(command_line_value=None):
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


def validate_config(config):
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
        "Slack": ["api_token", "bot_id", "channels"],
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

    if result:
        while config['ZoneMinder']['url'].endswith("/"):
            # We need the URL in a consistent format as some of the API calls
            # fail if there are too many slashes. I decided on no trailing slash
            #  as the default format
            config['ZoneMinder']['url'] = config['ZoneMinder']['url'][:-1]

    # Finally
    return result
