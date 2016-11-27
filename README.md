# ZoneMinder Slack Bot

This is a [Slack Bot](https://api.slack.com/bot-users) that monitors one or more [Slack](https://slack.com) channels for commands and interacts with a [ZoneMinder](https://www.zoneminder.com/) system to report events and
obtain information.

The primary use for this bot is to allow access to some parts of a ZoneMinder system that is behind a firewall, without having to expose the actual system to the Internet. Making a ZoneMinder system available to the Internet has several requirements (static IP, secure system) that may not be feasible for all users.

By providing a bot that can interact with both ZoneMinder and Slack, remote access to and notification from ZoneMinder is possible, without needing a static IP and using the security provided by the Slack environment.

[![Screen cast of basic features](https://raw.githubusercontent.com/rjclark/zoneminder-slack-bot/master/docs/images/ZoneBot-Screen-Cast-Static.png)](https://rjclark.github.io/zoneminder-slack-bot/docs/images/ZoneBot-Screen-Cast.webm)

## Installation

### Easiest : Using pip

The easiest method of installation is via `pip` as the package is available from the [Python Package Index](https://pypi.python.org/pypi)

```sh
> pip install zonebot
```    

This will create a script called `zonebot` in your path ("`which zonebot`" will tell you exactly where) that you can run.

### Download source and build

You can download the source from GitHub and build it yourself if you would like.

1. Download the release you want from https://github.com/rjclark/zoneminder-slack-bot/releases
1. Extract it
1. Run `python setup.py build install`

### Clone the source and build

You can also clone the source from GitHub if you would like to build the very latest version. **This is not guaranteed to work**. The unreleased source code from GitHub could be in the middle of development and running it directly is not recommended.

1. Clone this repository https://github.com/rjclark/zoneminder-slack-bot
1. Run `python setup.py build install`

## Configuration

Also installed is a sample configuration file called `zonebot-example-config.cfg`. You can copy this to your preferred location for config files and edit it to put in your [Slack API token](https://api.slack.com/tokens) and the [ID of your bot user](https://api.slack.com/bot-users)

The example configuration file is installed into the Python package directory on your system, which can be somewhat difficult to find. The latest version of the file is always available from [the GitHub repository](https://github.com/rjclark/zoneminder-slack-bot/blob/master/docs/zonebot-example-config.cfg) if needed.

To configure the bot, you will need several pieces of information

1. Your Slack API token. This can be found by
    1. Going to the [Slack Bot user page](https://api.slack.com/bot-users) and creating a new bot user. You will have a chance to get the API token here
    2. Going to the page for your [existing bot user](https://my.slack.com/apps/manage/custom-integrations).
2. The User ID of your bot user. This can be found by:
    1. Running the script `zonebot-getid` distributed with this package and providing the name of the Slack bot user and you Slack API token as command line options. For example:

```sh
> zonebot-getid  -a "your-slack-token" -b zoneminder
> User ID for bot 'zoneminder' is AA22BB44C
```

Once you have those, make a copy of the config file and add the Slack API token and user ID of the bot, You will also want to edit the `Permissions` section.

**NOTE**: The default config file allows only read permission to the ZoneMinder system.

The default config file can be placed in any of these locations (checked in this order)

* Any file specified by the `-c/--config` command line option
* `$XDG_CONFIG_HOME/zonebot/zonebot.conf` if the `XDG_CONFIG_HOME` environment variable is defined
* `${DIR}/zonebot/zonebot.conf` for any directory in the `XDG_CONFIG_DIRS` environment variable
* `~/.config/zonebot/zonebot.conf`
* `/etc/zonebot/zonebot.conf`
* `/etc/default/zonebot`

## Reporting Problems

1. The best way to report problems is to log a report on the GitHub Issues page [https://github.com/rjclark/zoneminder-slack-bot/issues](https://github.com/rjclark/zoneminder-slack-bot/issues) for this project. 
2. If you do not have a GItHub account, you can also contact me via email: [clark@exiter.com](mailto:clark@exiter.com)

## Building and Contributing

If you wish to contribute, pull requests against the [GitHub repository](https://github.com/rjclark/zoneminder-slack-bot) are welcomed.

[![Build Status](https://travis-ci.org/rjclark/zoneminder-slack-bot.svg?branch=master)](https://travis-ci.org/rjclark/zoneminder-slack-bot)
[![Coverage Status](https://coveralls.io/repos/github/rjclark/zoneminder-slack-bot/badge.svg?branch=master)](https://coveralls.io/github/rjclark/zoneminder-slack-bot?branch=master)
[![PyPI version](https://badge.fury.io/py/zonebot.svg)](https://pypi.python.org/pypi/zonebot)
[![Dependency Status](https://www.versioneye.com/user/projects/57def689037c2000458f770d/badge.svg?style=flat-square)](https://www.versioneye.com/user/projects/57def689037c2000458f770d)
[![Code Health](https://landscape.io/github/rjclark/zoneminder-slack-bot/master/landscape.svg?style=flat)](https://landscape.io/github/rjclark/zoneminder-slack-bot/master)

### Requirements and Tools

If you are new to the concept of building either a Python application or a Slack bot, I encourage you to review the excellent posting over at [Full Stack Python](https://www.fullstackpython.com) called
[How to Build Your First Slack Bot with Python](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html). This document will provide a summary of the requirements and steps necessary, but it assumes a basica familiarity with the tools and environment that the linked article covers in some depth.

This list of tools from the [First Slack Bot](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html) blog is all that is needed to build this bot.

> * Either [Python 2 or 3](https://wiki.python.org/moin/Python2orPython3)
> * [pip](https://pip.pypa.io/en/stable/) and [virtualenv](https://virtualenv.pypa.io/> en/stable/) to handle Python application dependencies
> * A [Slack account](https://slack.com/) with a team on which you have API access.
> * Official Python [slackclient](https://github.com/slackhq/python-slackclient) code library built by the Slack team
> * [Slack API testing token](https://api.slack.com/tokens)
>
> It is also useful to have the [Slack API docs](https://api.slack.com/) handy while you're building this tutorial.

### Setup

1. Use `virtualenv` and `pip` to create a development

```sh
> virtualenv venv
> source venv/bin/activate
    (or . venv/bin/activate.fish of you use the fish shell)

> venv/bin/pip install install -r requirements.txt
```

2. Obtain a Slack API token (and optionally create a dedicated [bot user](https://api.slack.com/bot-users) for the API token) from Slack

3. Since the API token needs to remain secret, you should set it as an environment
variable rather than putting it into any source file.

```sh
> export SLACK_BOT_TOKEN='your slack token pasted here'
```

4. Run `utils/get_bot_id.py` to get the number ID of the bot (as opposed to the name you gave the bot user. This is also our first real test of the API token

5. Put the bot ID into an environment variable as well.

```sh
> export BOT_ID='bot id returned by script'
```

Later on the BOT_ID and SLACK_API_TOKEN (along with a lot of the other config options) will be loaded from a config file. This is to make running the script as a daemon less of a hassle.
