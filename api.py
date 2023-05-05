"""interface for app functionality"""

import logging
import os

import replicate
from slack_sdk.errors import SlackApiError


logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

def _is_replicate_enabled():
    return os.environ["IS_REPLICATE_API_ENABLED"].lower() == "true"


def respond_direct_invocation(body):
    text = body["text"]
    image_urls = run_stable_diffusion(text)
    urls_message = "\n".join(image_urls)
    return f"> {text}\n{urls_message}"


def run_stable_diffusion(prompt):
    STABLE_DIFFUSION_V_2_1 = "db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf"
    if _is_replicate_enabled():
        output = replicate.run(
            f"stability-ai/stable-diffusion:{STABLE_DIFFUSION_V_2_1}",
            input={"prompt": prompt}
        )
    else:
        output = [get_random_color_image()]  # default if api is disabled
    return output


def get_random_color_image():
    """https://www.geeksforgeeks.org/create-random-hex-color-code-using-python/"""
    import random

    # Generating a random number in between 0 and 2^24
    color = random.randrange(0, 2**24)

    # Converting that number from base-10
    # (decimal) to base-16 (hexadecimal)
    hex_color = hex(color)[2:]

    return f"https://www.colorhexa.com/{hex_color}.png"


def respond_mention(client, body):
    event = body["event"]
    if _is_event_threaded(event):
        # TODO: get whole thread
        logger.debug("~~~THREADED_EVENT~~~")
    else:
        # TODO: get conversation history as input
        # TODO: remove mrkdwn
        image_outputs = run_stable_diffusion(event["text"])
        image_message = "\n".join(image_outputs)
        reply_to_thread(client, event, image_message)


def reply_to_thread(client, message_event, message_content):
    if _is_event_threaded(message_event):
        parent_ts = message_event["thread_ts"]
    else:
        parent_ts = message_event["ts"]
    try:
        # Call the chat.postMessage method using the WebClient
        result = client.chat_postMessage(
            channel=message_event["channel"],
            thread_ts=parent_ts,
            text=message_content
            # You could also use a blocks[] array to send richer content
        )

        logger.debug("postMessage result=%s", result)

    except SlackApiError as e:
        logger.error(f"Error posting message exc={e}")


def _is_event_threaded(event):
    return "thread_ts" in event


