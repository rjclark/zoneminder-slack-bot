Building ZoneMinder-Slack-Bot
=============================

Requirements and Tools
----------------------

If you are new to the concept of building either a Python application or a Slack
bot, I encourage you to review the excellent posting over at
[Full Stack Python](https://www.fullstackpython.com) called
[How to Build Your First Slack Bot with Python](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html). This document will provide a summary of the
requirements and steps necessary, but it assumes a basica familiarity with the
tools and environment that the linked article covers in some depth.

This list of tools from the [First Slack Bot](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html) blog is all that is needed
to build this bot.

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

    \# virtualenv venv
    \# source venv/bin/activate
    (or . venv/bin/activate.fish of you use the fish shell)

    \# venv/bin/pip install install -r requirements.txt

2. Obtain a Slack API token (and optionally create a dedicated [bot user](https://api.slack.com/bot-users) for the API token) from Slack

3. Since the API token needs to remain secret, you should set it as an environment
variable rather than putting it into any source file.

    \# export SLACK_BOT_TOKEN='your slack token pasted here'

4. Run `utils/get_bot_id.py` to get the number ID of the bot (as opposed to the nameyou gave the bot user. This is also our first real test of the API token

5. Put the bot ID into a n environment variable as well.

    \# export BOT_ID='bot id returned by script'

Later on the BOT_ID and SLACK_API_TOKEN (along with a lot of the other config options
will be loaded from a config file. This is to make running the script as a daemon less of
a hassle.
