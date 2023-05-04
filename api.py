"""interface for app functionality"""

from dataclasses import dataclass
import replicate

def respond_direct_invocation(client, body):
    text = body["text"]
    image_urls = run_stable_diffusion(text)
    urls_message = "\n".join(image_urls)
    message_text = f"here is my response: https://www.colorhexa.com/c13064.png \n{text}\n{urls_message}"
    channel = body["channel_id"]
    client.chat_postMessage(
        channel=channel,
        text=message_text,
    )


def run_stable_diffusion(prompt):
    STABLE_DIFFUSION_V_2_1 = "db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf"
    output: list = replicate.run(
        f"stability-ai/stable-diffusion:{STABLE_DIFFUSION_V_2_1}",
        input={"prompt": prompt}
    )
    return output


@dataclass
class StableDiffusionOutput:
    output: list
