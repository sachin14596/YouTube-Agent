"""
Shared AWS Bedrock model helper
--------------------------------
Handles LLM calls through AWS Bedrock Runtime.
Ensures unified prompt formatting & decoding for all tools.
"""

import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

# === AWS CONFIG ===
REGION = os.getenv("AWS_REGION", "us-west-2")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "meta.llama3-8b-instruct-v1:0")

# === Client ===
try:
    bedrock_client = boto3.client("bedrock-runtime", region_name=REGION)
    print(f"✅ Bedrock client initialized ({MODEL_ID}) in {REGION}")
except Exception as e:
    print(f"❌ Failed to init Bedrock client: {e}")
    bedrock_client = None


def generate_bedrock_response(prompt: str, max_tokens: int = 500, temperature: float = 0.7):
    """
    Sends a text prompt to AWS Bedrock model and returns generated text.
    """
    if not bedrock_client:
        raise RuntimeError("Bedrock client not initialized")

    formatted_prompt = f"""
    <|begin_of_text|><|start_header_id|>user<|end_header_id|>
    {prompt}
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """

    payload = {
        "prompt": formatted_prompt.strip(),
        "max_gen_len": max_tokens,
        "temperature": temperature,
    }

    try:
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(payload),
            contentType="application/json"
        )
        result = json.loads(response["body"].read())
        return result.get("generation", "").strip()
    except ClientError as e:
        print(f"⚠️ AWS ClientError: {e}")
        return ""
    except Exception as e:
        print(f"⚠️ Bedrock inference error: {e}")
        return ""
