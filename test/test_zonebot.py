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

import os
from nose.tools import assert_equal
import zonebot
from zonebot.bot import ZoneBot
import logging
import json

from configparser import ConfigParser

logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("zonebot").disabled = True


def test_command_detection():
    config = __load_config()

    zb = ZoneBot(config)

    # Now do some parsing

    # Basic command to the bot
    data = json.loads(""" {
                      "channel": "AABBCC",
                      "team": "EEFFGG",
                      "text": "<@HHIIJJ>  hello",
                      "ts": "1473574250.000010",
                      "type": "message",
                      "user": "KKLLMM"
                      } """)
    user, channel, command = zb._extract_command(data, '<@HHIIJJ>')

    assert user
    assert channel
    assert command

    assert_equal(user, "KKLLMM")
    assert_equal(channel, "AABBCC")
    assert_equal(command, "hello")

    # Message not to the bot
    data = json.loads(""" {
                      "channel": "AABBCC",
                      "team": "EEFFGG",
                      "text": "<@AABBCC>  hello",
                      "ts": "1473574250.000010",
                      "type": "message",
                      "user": "KKLLMM"
                      } """)
    user, channel, command = zb._extract_command(data, '<@HHIIJJ>')

    assert not user
    assert not command
    assert not channel

    # Not a message at all
    data = json.loads(""" {
                      "ping": "a",
                      "pong": "b"
                      } """)
    user, channel, command = zb._extract_command(data, '<@HHIIJJ>')

    assert not user
    assert not command
    assert not channel


def __load_config():
    example_config = os.path.join(os.path.dirname(__file__),
                                  "..",
                                  "etc",
                                  "zonebot-example-config.cfg")

    config = ConfigParser()
    config.read(example_config)

    zonebot.validate_config(config)

    return config
