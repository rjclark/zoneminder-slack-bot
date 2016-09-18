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

import argparse
import logging
import sys

from configparser import ConfigParser
import zonebot
from zonebot.bot import ZoneBot

LOGGER = logging.getLogger("zonebot")


def zonebot_main():
    """
    Main method for the zonebot script
    """

    # basic setup
    zonebot.init_logging(None)

    #  Set up the command line arguments we support
    parser = argparse.ArgumentParser(description='A Slack bot to interact with ZoneMinder',
                                     epilog="Version " + zonebot.__version__ + " (c) " + zonebot.__author__)

    parser.add_argument('-c', '--config',
                        metavar='file',
                        required=False,
                        help='Load the specified config file')

    args = parser.parse_args()

    # Create the configuration from the arguments
    config = ConfigParser()
    config_file = zonebot.find_config(args.config)
    if config_file:
        config.read(config_file)
    else:
        LOGGER.error("No config file could be located")
        sys.exit(1)

    if not zonebot.validate_config(config):
        sys.exit(1)

    LOGGER.debug("Configuration is valid")

    # Reconfigure logging with config values
    zonebot.init_logging(config)

    LOGGER.info("Starting up")
    LOGGER.info("Version %s", zonebot.__version__)

    bot_process = ZoneBot(config)
    bot_process.start()



