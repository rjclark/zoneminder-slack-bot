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
from zonebot import ZoneBot
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


def test_permission_no_section():
    """ When there is no permission section, anyone can do anything. """
    config = __load_config()
    zb = ZoneBot(config)
    zb._usermap['me'] = 'me'

    config.remove_section('Permissions')

    # any permission
    assert zb._has_permission('me', 'help')

    # read permission

    # write permission
    assert zb._has_permission('me', 'enable')
    assert zb._has_permission('me', 'disable')

    # unknown command, never allowed
    assert not zb._has_permission('me', 'something else')


def test_permission_empty_section():
    """ When there is a permission section, but no entries, everyone gets read access. """
    config = __load_config()
    zb = ZoneBot(config)
    zb._usermap['me'] = 'me'

    config.remove_section('Permissions')
    config.add_section('Permissions')

    # any permission
    assert zb._has_permission('me', 'help')

    # read permission

    # write permission
    assert not zb._has_permission('me', 'enable')
    assert not zb._has_permission('me', 'disable')

    # unknown command, never allowed
    assert not zb._has_permission('me', 'something else')


def test_permission_read():
    """ 'read' permission is any command that is marked with 'read' """
    config = __load_config()
    zb = ZoneBot(config)
    zb._usermap['me'] = 'me'

    config.remove_section('Permissions')
    config.add_section('Permissions')
    config.set('Permissions', 'me', 'read')

    # any permission
    assert zb._has_permission('me', 'help')

    # read permission

    # write permission
    assert not zb._has_permission('me', 'enable')
    assert not zb._has_permission('me', 'disable')

    # unknown command, never allowed
    assert not zb._has_permission('me', 'something else')


def test_permission_write():
    """ 'write' permission is any command that is marked with 'write' """
    config = __load_config()
    zb = ZoneBot(config)
    zb._usermap['me'] = 'me'

    config.remove_section('Permissions')
    config.add_section('Permissions')
    config.set('Permissions', 'me', 'write')

    # any permission
    assert zb._has_permission('me', 'help')

    # read permission

    # write permission
    assert zb._has_permission('me', 'enable')
    assert zb._has_permission('me', 'disable')

    # unknown command, never allowed
    assert not zb._has_permission('me', 'something else')


def test_permission_any():
    """ 'write' permission is any command that is marked with 'write' """
    config = __load_config()
    zb = ZoneBot(config)
    zb._usermap['me'] = 'me'

    config.remove_section('Permissions')
    config.add_section('Permissions')
    config.set('Permissions', 'me', 'any')

    # any permission
    assert zb._has_permission('me', 'help')

    # read permission

    # write permission
    assert zb._has_permission('me', 'enable')
    assert zb._has_permission('me', 'disable')

    # unknown command, never allowed
    assert not zb._has_permission('me', 'something else')


def test_permission_command():
    """ 'write' permission is any command that is marked with 'write' """
    config = __load_config()
    zb = ZoneBot(config)
    zb._usermap['me'] = 'me'

    config.remove_section('Permissions')
    config.add_section('Permissions')
    config.set('Permissions', 'me', 'disable')

    # any permission
    assert zb._has_permission('me', 'help')

    # read permission

    # write permission
    assert not zb._has_permission('me', 'enable')
    assert zb._has_permission('me', 'disable')  # this is the only non-any command allowed

    # unknown command, never allowed
    assert not zb._has_permission('me', 'something else')


def __load_config():
    example_config = os.path.join(os.path.dirname(__file__),
                                  "..",
                                  "docs",
                                  "zonebot-example-config.cfg")

    config = ConfigParser()
    config.read(example_config)

    zonebot._validate_config(config)

    return config
