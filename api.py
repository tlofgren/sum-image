"""interface for app functionality"""

import os
import replicate

def _is_replicate_enabled():
    return os.environ["IS_REPLICATE_API_ENABLED"].lower() == "true"


def respond_direct_invocation(body):
    text = body["text"]
    image_urls = run_stable_diffusion(text)
    urls_message = "\n".join(image_urls)
    return f"> {text}\n{urls_message}"


def run_stable_diffusion(prompt):
    STABLE_DIFFUSION_V_2_1 = "db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf"
    output = [get_random_color_image()]  # default if api is disabled
    if _is_replicate_enabled():
        output = replicate.run(
            f"stability-ai/stable-diffusion:{STABLE_DIFFUSION_V_2_1}",
            input={"prompt": prompt}
        )
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

