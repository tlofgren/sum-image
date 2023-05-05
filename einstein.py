"""Custom client for interacting with the Einstein GPT API"""
import logging
import requests

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

class EinsteinClient:
    def __init__(self, gateway_url, api_key, org_id, llm_provider) -> None:
        self.gateway_url = gateway_url
        self.api_key = api_key
        self.org_id = org_id
        self.llm_provider = llm_provider
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-LLM-Provider": self.llm_provider,
                "X-Org-Id": self.org_id,
                "Authorization": f"API_KEY {self.api_key}",
            }
        )

    def generate_completions(self, prompt, temperature=0.7):
        url = f"{self.gateway_url}/v1.0/generations"

        payload ={
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": 512,
        }
        # headers = {
        #     "Content-Type": "application/json",
        #     "X-LLM-Provider": LLM_PROVIDER,
        #     "X-Org-Id": SFDC_ORG_ID,
        #     "Authorization": f"API_KEY {EINSTEIN_API_KEY}",
        # }
        # Ignore issue with local SSL certs
        response = self.session.post(url, json=payload, verify=False)
        return response


def _test_client():
    from dotenv import load_dotenv
    load_dotenv()
    from api import EINSTEIN_API_KEY, EINSTEIN_GATEWAY, LLM_PROVIDER, SFDC_ORG_ID

    client = EinsteinClient(EINSTEIN_GATEWAY, EINSTEIN_API_KEY, SFDC_ORG_ID, LLM_PROVIDER)
    response = client.generate_completions("write a limerick about the perils of greed")
    print(response.status_code, response.json())
    client.session.close()


if __name__ == "__main__":
    _test_client()
    exit()
