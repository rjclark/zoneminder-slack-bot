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
    assert not zonebot._validate_config(None)


def test_empty_config():
    config = ConfigParser()
    assert not zonebot._validate_config(config)


def test_example_config_valid():
    example_config = os.path.join(os.path.dirname(__file__), "..", "docs", "zonebot-example-config.cfg")

    assert os.path.isfile(example_config)

    config = ConfigParser()
    config.read(example_config)


