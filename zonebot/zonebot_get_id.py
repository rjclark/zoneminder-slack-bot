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
A utility to determine the ID fo the Slack user assigned as the bot.
"""

import sys
import argparse
from slackclient import SlackClient

import zonebot


def zonebot_getid_main():
    """
    Main method for the util script that figures out the bot ID
    """

    #  Set up the command line arguments we support
    parser = argparse.ArgumentParser(description='Find the ID for a Slack bot user',
                                     epilog="Version " + zonebot.__version__ + " (c) " +
                                            zonebot.__author__ +
                                            " (" + zonebot.__email__ + ")")

    parser.add_argument('-a', '--apitoken',
                        metavar='key',
                        required=True,
                        help='Slack API token')

    parser.add_argument('-b', '--botname',
                        metavar='name',
                        required=True,
                        help='Name of the Slack bot user to search for')

    args = parser.parse_args()

    slack_client = SlackClient(args.apitoken)
    api_call = slack_client.api_call("users.list")

    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name').lower() == args.botname.lower():
                print("User ID for bot '{0}' is {1}".format(user['name'], user.get('id')))
                sys.exit(0)
    else:
        print("Slack API call failed (invalid API token?")

    # Not found
    print("Could not find bot user with the name {0}".format(args.botname))
    sys.exit(1)
