ZoneMinder Slack Bot
====================

This is a [Slack Bot](https://api.slack.com/bot-users) that monitors one or
more (Slack)[https://slack.com] channels for commands and interacts with
a [ZoneMinder](https://www.zoneminder.com/) system to report events and
obtain information.

The primary use for this bot is to allow access to some parts of a ZoneMinder
system that is behind a firewall, without having to expose the actual system
to the Internet. Making a ZoneMinder system available to the Internet has
several requirements (static IP, secure system) that may not be feasible for all
users.

By providing a bot that can interact with both ZoneMinder and Slack, remote
access to and notification from ZoneMinder is possible, without needing a static
IP and using the security provided by the Slack environment.

**NOTE:** If you are only interested in installing and running the bot from a existing
package, then please refer to the `INSTALLING.md` document, This document explains how
to build and package the bot.

Requirements and Tools
----------------------

If you are new to the concept of building either a Python application or a Slack
bot, I encourage you to review the excellent posting over at 
[Full Stack Python](https://www.fullstackpython.com) called
[How to Build Your First Slack Bot with Python](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html). This document will provide a summary of the 
requirements and steps necessary, but it assumes a basica familiarity with the
tools and environment that the linked article covers in some depth.

This list of tools from the [First Slack Bot](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html) blog is all that is needed
to buil this bot.

> * Either [Python 2 or 3](https://wiki.python.org/moin/Python2orPython3)
> * [pip](https://pip.pypa.io/en/stable/) and [virtualenv](https://virtualenv.pypa.io/> en/stable/) to handle Python application dependencies
> * A [Slack account](https://slack.com/) with a team on which you have API access.
> * Official Python [slackclient](https://github.com/slackhq/python-slackclient) code library built by the Slack team
> * [Slack API testing token](https://api.slack.com/tokens)
>
> It is also useful to have the [Slack API docs](https://api.slack.com/) handy while you're building this tutorial.

Setup
-----

1. Use `virtualenv` and `pip` to create a development 

    \# virtualenv zoneminder-slack-bot  
    \# source zoneminder-slack-bot/bin/activate  
    (or . zoneminder-slack-bot/bin/activate.fish of you use the fish shell)

    \# zoneminder-slack-bot/bin/pip install slackclient

2. Obtain a Slack API token (and optionally create a dedicated [bot user](https://api.slack.com/bot-users) for the API token) from Slack

3. Since the API token needs to remain secret, you should set it as an environment
variable rather than putting it into any source file.

    \# export SLACK_BOT_TOKEN='your slack token pasted here'

4. Run `utils/get_bot_id.py` to get the number ID of the bot (as opposed to the nameyou gave the bot user. This is also our first real test of the API token

5. Put the bot ID into a n environment variable as well.

    \# export BOT_ID='bot id returned by script'

    