#!/usr/bin/env python
#! -*- coding: utf-8 -*-

"""
Utility to obtain the number ID for a Slack user (bot)

This example code is from https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
(c) Matt Makai

"""
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from slackclient import SlackClient


BOT_NAME = 'zoneminder'

SLACK_CLIENT = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

if __name__ == "__main__":
    API_CALL = SLACK_CLIENT.api_call("users.list")
    if API_CALL.get('ok'):
        # retrieve all users so we can find our bot
        USERS = API_CALL.get('members')
        for user in USERS:
            if 'name' in user and user.get('name') == BOT_NAME:
                print "Bot ID for '{0}' is {1}".format(user['name'], user.get('id'))
    else:
        print "could not find bot user with the name {0}".format(BOT_NAME)
