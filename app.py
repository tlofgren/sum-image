import logging
import os

logging.basicConfig(level=logging.DEBUG)

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.adapter.socket_mode import SocketModeHandler

from api import respond_direct_invocation

app = App(token=os.environ["SLACK_BOT_TOKEN"])


@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()


@app.command("/sum-image")
def handle_slash_command(ack, say, command, client, body, logger):
    logger.debug("command=%s body=%s", command, body)
    ack()
    respond_direct_invocation(client, body)


@app.event("app_mention")
def handle_app_mention(body, say, logger):
    logger.info(body)
    say("What's up?")


@app.event("message")
def handle_message():
    pass


from flask import Flask, request

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/")
def home():
    return "Hello, Flask!"


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


# if __name__ == "__main__":
SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

# pip install -r requirements.txt
# export SLACK_SIGNING_SECRET=***
# export SLACK_BOT_TOKEN=xoxb-***
# FLASK_APP=app.py FLASK_ENV=development flask run -p 3000
