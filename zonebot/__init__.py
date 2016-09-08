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
import logging
import argparse
import ConfigParser

VERSION = '1.0'
AUTHOR = 'Robert Clark <clark@exiter.com>'

LOGGER = logging.getLogger("zonebot")

def init_logging(config):
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
    REQUIRED = {
        "Slack" : ["api_token", "bot_id"],
        "ZoneMinder" : ["url", "username", "password"]
    }

    result = True

    for section in REQUIRED.iterkeys():
        if not config.has_section(section):
            LOGGER.error("No [{0}] section in the configuration".format(section))
            result = False
        else:
            for option in REQUIRED[section]:
                if not config.has_option(section, option):
                    LOGGER.error("Required option {0} missing from section [{1}]".format(option, section))
                    result = False

    # Finally
    return result

def main():
    #  Set up the command line arguments we support
    PARSER = argparse.ArgumentParser(description='A Slack bot to interact with ZoneMinder',
                                     epilog="Version " + VERSION + " (c) " + AUTHOR)

    PARSER.add_argument('-c', '--config',
                        type=argparse.FileType('r'),
                        metavar='file',
                        required=True,
                        help='Load the specific config file')

    ARGS = PARSER.parse_args()

    # Create the configuration from the arguments
    config = ConfigParser.ConfigParser()
    if ARGS.config:
        config.readfp(ARGS.config)
        ARGS.config.close()

    init_logging(config)

    LOGGER.info("Starting up")
    LOGGER.info("Version {}".format(VERSION))

    if not validate_config(config):
        sys.exit(1)

    LOGGER.info("Configuration is valid")
