"""
Shared global model loader for all tools (rewrite, title-thumb, policy).
Ensures single memory instance for meta-llama/Llama-3.2-1B-Instruct.
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"

print(f"🧠 Initializing shared global model: {MODEL_NAME} ...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

print(f"✅ Model loaded on {device}")

__all__ = ["model", "tokenizer", "device", "MODEL_NAME"]
