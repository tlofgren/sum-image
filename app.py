import logging
import os
from typing import Callable

logging.basicConfig(level=logging.DEBUG)

from slack_bolt import App, Say, BoltContext
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient


from api import respond_direct_invocation, respond_mention

app = App(token=os.environ["SLACK_BOT_TOKEN"])


@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()


def extract_subtype(body: dict, context: BoltContext, next: Callable):
    """https://github.com/slackapi/bolt-python/blob/main/examples/message_events.py"""
    context["subtype"] = body.get("event", {}).get("subtype", None)
    next()


@app.command("/sum-image")
def handle_slash_command(ack, say, client, body, logger):
    logger.debug("slash command body=%s", body)
    ack()
    response = respond_direct_invocation(body)
    say(response)


@app.event("app_mention")
def handle_app_mention(ack, say, client, body, logger):
    ack()
    logger.debug("handle_app_mention body=%s", body)
    respond_mention(client, body)
    # say("What's up?")


@app.event("message")
def handle_message(message, say, logger):
    logger.debug("event message message=%s", message)
    if _is_message_im(message):
        logger.debug("YES, this is an IM")
        response = respond_direct_invocation(message)
        say(response)
    else:
        logger.debug("NOT IM")


def _is_message_im(message):
    return message["channel_type"] == "im"


# This listener handles all uncaught message events
# (The position in source code matters)
@app.event({"type": "message"}, middleware=[extract_subtype])
def just_ack(logger, context):
    """https://github.com/slackapi/bolt-python/blob/main/examples/message_events.py"""
    subtype = context["subtype"]  # by extract_subtype
    logger.info(f"{subtype} is ignored")


# from flask import Flask, request

# flask_app = Flask(__name__)
# handler = SlackRequestHandler(app)


# @flask_app.route("/slack/events", methods=["POST"])
# def slack_events():
#     return handler.handle(request)


# if __name__ == "__main__":
SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

# pip install -r requirements.txt
# export SLACK_SIGNING_SECRET=***
# export SLACK_BOT_TOKEN=xoxb-***
# FLASK_APP=app.py FLASK_ENV=development flask run -p 3000
