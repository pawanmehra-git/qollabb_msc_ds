"""
Ollama (Mistral) integration for context-aware generation.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "mistral")

# Sampling controls for deterministic-ish outputs.
# If you want consistent answers, prefer temperature=0 and a fixed seed.
DEFAULT_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.0"))
DEFAULT_TOP_K = int(os.environ.get("OLLAMA_TOP_K", "1"))
DEFAULT_TOP_P = float(os.environ.get("OLLAMA_TOP_P", "1.0"))
DEFAULT_SEED = int(os.environ.get("OLLAMA_SEED", "42"))


def generate_response(
    prompt: str,
    context: str = "",
    model: str | None = None,
    temperature: float | None = None,
    top_k: int | None = None,
    top_p: float | None = None,
    seed: int | None = None,
) -> str:
    """
    Call Ollama's chat/generate API with optional conversation and RAG context.

    :param prompt: User message (or task text).
    :param context: System/context block (FAQ snippets, book list summary, history).
    """
    model = model or DEFAULT_MODEL
    host = DEFAULT_OLLAMA_HOST.rstrip("/")

    system_parts: list[str] = [
        "You are Ansira, a helpful assistant for Ansira Book Shop.",
        "Be concise, friendly, and accurate. If context is provided, prefer it over guessing.",
    ]
    if context.strip():
        system_parts.append("Context:\n" + context.strip())

    full_prompt = "\n\n".join(system_parts) + "\n\nUser:\n" + prompt.strip()

    url = f"{host}/api/generate"
    # Pull sampling parameters from env if not provided by caller.
    temperature = DEFAULT_TEMPERATURE if temperature is None else temperature
    top_k = DEFAULT_TOP_K if top_k is None else top_k
    top_p = DEFAULT_TOP_P if top_p is None else top_p
    seed = DEFAULT_SEED if seed is None else seed

    payload: dict[str, Any] = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
            "seed": seed,
        },
    }

    try:
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        text = data.get("response", "").strip()
        if not text:
            return (
                "I could not get a response from the language model. "
                "Please ensure Ollama is running and the model is pulled: `ollama pull mistral`."
            )
        return text
    except requests.exceptions.ConnectionError:
        logger.exception("Ollama connection failed")
        return (
            "Cannot reach Ollama. Start the Ollama app and ensure the Mistral model is available "
            "(`ollama pull mistral`), then try again."
        )
    except requests.exceptions.Timeout:
        logger.exception("Ollama timeout")
        return "The request timed out. Please try a shorter message or try again."
    except requests.exceptions.RequestException as e:
        logger.exception("Ollama request failed: %s", e)
        return f"Error talking to the AI service: {e!s}"


def extract_entities_llm(
    user_text: str,
    fields_description: str,
    model: str | None = None,
) -> str:
    """
    Optional helper: ask the model to return JSON-like key values for entities.
    Returns raw model output for parsing by the caller.
    """
    model = model or DEFAULT_MODEL
    host = DEFAULT_OLLAMA_HOST.rstrip("/")
    prompt = (
        f"Extract structured data from the user message. Only output a single JSON object, no markdown.\n"
        f"Fields to extract: {fields_description}\n"
        f"User message: {user_text!r}\n"
        "If a field is unknown, use null."
    )
    url = f"{host}/api/generate"
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": DEFAULT_TEMPERATURE,
            "top_k": DEFAULT_TOP_K,
            "top_p": DEFAULT_TOP_P,
            "seed": DEFAULT_SEED,
        },
    }
    try:
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception:
        logger.exception("LLM entity extraction failed")
        return ""
