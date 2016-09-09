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

VERSION = '1.0'
AUTHOR = 'Robert Clark <clark@exiter.com>'

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


def zonebot_main():
    """
    Main method for the zonebot script
    """

    #  Set up the command line arguments we support
    parser = argparse.ArgumentParser(description='A Slack bot to interact with ZoneMinder',
                                     epilog="Version " + VERSION + " (c) " + AUTHOR)

    parser.add_argument('-c', '--config',
                        type=argparse.FileType('r'),
                        metavar='file',
                        required=True,
                        help='Load the specific config file')

    args = parser.parse_args()

    # Create the configuration from the arguments
    config = ConfigParser()
    if args.config:
        config.read_file(args.config)
        args.config.close()

    _init_logging(config)

    LOGGER.info("Starting up")
    LOGGER.info("Version %s", VERSION)

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
        epilog="Version " + VERSION + " (c) " + AUTHOR)

    parser.add_argument('event_dir',
                        help='The directory in which the event files are stored')

    args = parser.parse_args()

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

    print('monitor:   {}'.format(monitor))
    print('timestamp: {}'.format(timestamp))
