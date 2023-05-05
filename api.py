"""interface for app functionality"""

import json
import logging
import os

# from flask import render_template
from jinja2 import Environment, FileSystemLoader
import replicate
from slack_sdk.errors import SlackApiError

from einstein import EinsteinClient

EINSTEIN_GATEWAY = os.environ["EINSTEIN_GATEWAY"]
EINSTEIN_API_KEY = os.environ["EINSTEIN_API_KEY"]
SFDC_ORG_ID = os.environ["SFDC_ORG_ID"]
LLM_PROVIDER = "OpenAI"
DEFAULT_IMAGE_PROMPT = "sketch of robot contemplating its reflection in a mirror while holding a paintbrush"


logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

einstein = EinsteinClient(EINSTEIN_GATEWAY, EINSTEIN_API_KEY, SFDC_ORG_ID, LLM_PROVIDER)


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
        messages = get_thread_replies_from_event(client, event)
        logger.debug("preceding messages %s", json.dumps(messages))
        text_prompt = build_prompt_with_list(messages)
        image_prompt = get_text_completion(einstein, text_prompt)
    else:
        image_prompt = event["text"]
    if not image_prompt:
        image_prompt = DEFAULT_IMAGE_PROMPT
        # TODO: get conversation history as input
        # TODO: remove mrkdwn
    image_outputs = run_stable_diffusion(image_prompt)
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


def get_thread_replies_from_event(client, message_event):
    if _is_event_threaded(message_event):
        parent_ts = message_event["thread_ts"]
    else:
        parent_ts = message_event["ts"]
    try:
        result = client.conversations_replies(
            channel=message_event["channel"],
            ts=parent_ts,
            limit=100,
        )

        logger.debug("conversations_replies result=%s", result)
        return _get_preceding_replies(result["messages"], message_event["ts"])
    except SlackApiError as e:
        logger.error(f"Error fetching replies exc={e}")


def _get_preceding_replies(messages_list, target_reply_ts, max_num_preceding=2):
    """Given a list of thread replies from the Slack API, slice a number of replies leading up and including to the target reply.

    Args:
        messages_list (list): list of messages from conversations.replies or conversations.history
        target_reply_ts (str): ts of the reply we want to target as the latest reply to slice.
        max_num_preceding (int, optional): maximum number of replies from before the target one to slice out of the messages list. Defaults to 2.

    Returns:
        list: slice of the messages list with the replies preceding the target one, as well as the target
    """
    for i in range(len(messages_list) - 1, 0, -1):
        reply = messages_list[i]
        if reply["ts"] == target_reply_ts:
            start_idx = max(0, i - max_num_preceding)
            return messages_list[start_idx:i+1]  # include target reply


def _render_jinja_template(filename, context):
    environ = Environment(loader=FileSystemLoader("templates/"))
    template = environ.get_template(filename)
    return template.render(context)


def build_prompt_with_list(text_list):
    text_as_json = json.dumps(text_list)
    rendered_prompt = _render_jinja_template("prompt_keyword_image_generate_prompt.txt", {"json_array": text_as_json})
    logger.debug("rendered_prompt=%s", rendered_prompt)
    return rendered_prompt


def get_text_completion(client, prompt):
    response = client.generate_completions(prompt)
    if response.status_code != 200:
        logger.error("Error from Einstein API status_code=%s content=%s", response.status_code, response.text)
        return
    response_payload = response.json()
    logger.debug("einstein response=%s", response_payload)
    resp_generations = response_payload["generations"]
    if len(resp_generations) < 1:
        logger.warning("unexpected response: nothing generated")
        return ""
    return resp_generations[0]["text"]
