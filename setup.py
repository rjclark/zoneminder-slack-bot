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

from setuptools import setup

setup(
  name = 'zonebot',
  version = '1.0',

  description = 'A Slack bot to interact with ZoneMinder',

  packages = ['zonebot'], # this must be the same as the name above

  author = 'Robert Clark',
  author_email = 'clark@exiter.com',

  url = 'https://github.com/nogudnik/zoneminder-slack-bot', # use the URL to the github repo
  license = 'Apache',

  keywords = ['slack', 'zoneminder'], # arbitrary keywords

  include_package_data=True,

  classifiers = [
    "Programming Language :: Python",

    # How mature is this project? Common values are
    #   2 - Pre-Alpha
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 2 - Pre-Alpha',

    # Pick your license as you wish (should match "license" above)
    'License :: OSI Approved :: Apache Software License',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',

    "Topic :: Communications :: Chat",
  ],

  # List run-time dependencies here.  These will be installed by pip when
  # your project is installed. For an analysis of "install_requires" vs pip's
  # requirements files see:
  # https://packaging.python.org/en/latest/requirements.html
  install_requires=[
    'slackclient'
  ],

  tests_require = [
    'nose',
  ],

  # To provide executable scripts, use entry points in preference to the
  # "scripts" keyword. Entry points provide cross-platform support and allow
  # pip to create the appropriate form of executable for the target platform.
  entry_points={
      'console_scripts': [
          'zonebot=zonebot:main',
      ],
  },
)
