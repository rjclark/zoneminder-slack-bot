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

import zonebot
from nose.tools import assert_equal


def test_empty_string():
    result = zonebot.split_os_path('')
    assert_equal(0, len(result))


def test_single_element_unix():
    result = zonebot.split_os_path('/')

    assert_equal(1, len(result))
    assert_equal('/', result[0])


def test_many_elements_unix():
    result = zonebot.split_os_path('/a/b/c/d/e/f/g/h')

    assert_equal(9, len(result))
    assert_equal('/', result[0])
    assert_equal('a', result[1])
    assert_equal('b', result[2])
    assert_equal('c', result[3])
    assert_equal('d', result[4])
    assert_equal('e', result[5])
    assert_equal('f', result[6])
    assert_equal('g', result[7])
    assert_equal('h', result[8])


def test_trailing_slash():
    result = zonebot.split_os_path('/a/b/c/d/e/f/g/h/')

    assert_equal(9, len(result))
    assert_equal('/', result[0])
    assert_equal('a', result[1])
    assert_equal('b', result[2])
    assert_equal('c', result[3])
    assert_equal('d', result[4])
    assert_equal('e', result[5])
    assert_equal('f', result[6])
    assert_equal('g', result[7])
    assert_equal('h', result[8])


def test_relative_path():
    result = zonebot.split_os_path('a/b/c')

    assert_equal(3, len(result))
    assert_equal('a', result[0])
    assert_equal('b', result[1])
    assert_equal('c', result[2])
