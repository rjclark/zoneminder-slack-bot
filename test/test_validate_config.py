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
import logging

from configparser import ConfigParser

logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("zonebot").disabled = True


def test_null_config():
    assert not zonebot.validate_config(None)


def test_empty_config():
    config = ConfigParser()
    assert not zonebot.validate_config(config)


def test_example_config_valid():
    example_config = os.path.join(os.path.dirname(__file__), "..", "etc", "zonebot-example-config.cfg")

    assert os.path.isfile(example_config)

    config = ConfigParser()
    config.read(example_config)

    assert zonebot.validate_config(config)


def test_url_fixes():
   example_config = os.path.join(os.path.dirname(__file__), "..", "etc", "zonebot-example-config.cfg")
   config = ConfigParser()
   config.read(example_config)

   config['ZoneMinder']['url'] = 'https://sample/zm///////'
   assert zonebot.validate_config(config)
   assert config['ZoneMinder']['url'] == 'https://sample/zm'

   config['ZoneMinder']['url'] = 'https://sample/zm/'
   assert zonebot.validate_config(config)
   assert config['ZoneMinder']['url'] == 'https://sample/zm'

   config['ZoneMinder']['url'] = 'https://sample/zm'
   assert zonebot.validate_config(config)
   assert config['ZoneMinder']['url'] == 'https://sample/zm'


def test_no_config_file():
    try:
        zonebot.find_config(None)
        assert "No config available should have triggered an exception"
    except ValueError:
        #  exported
        pass


def test_command_line_config_file():
    example_config = os.path.join(os.path.dirname(__file__), "..", "etc", "zonebot-example-config.cfg")

    assert os.path.isfile(example_config)

    location = zonebot.find_config(example_config)

    assert_equal(example_config, location)


def test_user_config_located():
    user_dir = os.path.join(os.path.expanduser("~"), '.config', 'zonebot')

    if not os.path.isdir(user_dir):
        os.makedirs(user_dir)

    user_file = os.path.join(os.path.expanduser("~"), '.config', 'zonebot', 'zonebot.conf')

    try:
        handle = open(user_file, 'w')
        handle.write('Some text')
        handle.close()

        assert os.path.isfile(user_file)

        location = zonebot.find_config(None)

        assert_equal(user_file, location)
    finally:
        if os.path.isfile(user_file):
            os.remove(user_file)

