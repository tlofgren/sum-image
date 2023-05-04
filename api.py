"""interface for app functionality"""


def respond_direct_invocation(client, body):
    text = body["text"]
    channel = body["channel_id"]
    client.chat_postMessage(
        channel=channel,
        text="here is my response",
    )




