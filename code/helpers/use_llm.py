#!/usr/bin/env python3
"""Ask Gemini via LiteLLM for stock-related questions."""

from __future__ import annotations

import os
import sys
from typing import Callable

from dotenv import load_dotenv
import requests

try:
    from litellm import completion, exceptions as litellm_exceptions
except ImportError:  # pragma: no cover - informative error for missing dep
    completion = None
    litellm_exceptions = None


def _require_litellm() -> None:
    if completion is None:
        raise ImportError(
            "litellm is not installed. Please install it to use this feature."
        ) from None  # 'from None' hides the original messy traceback


def _is_not_found_error(exc: Exception) -> bool:
    if litellm_exceptions and isinstance(exc, litellm_exceptions.NotFoundError):
        return True
    message = str(exc).lower()
    return "not found" in message or "404" in message


def _list_gemini_models(api_key: str) -> list[str]:
    url = "https://generativelanguage.googleapis.com/v1beta/models"
    try:
        response = requests.get(url, params={"key": api_key}, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return []
    payload = response.json()
    models = payload.get("models")
    if not isinstance(models, list):
        return []

    names: list[str] = []
    for model in models:
        if not isinstance(model, dict):
            continue
        name = model.get("name")
        if not isinstance(name, str):
            continue
        if not name.startswith("models/"):
            continue
        methods = model.get("supportedGenerationMethods")
        if isinstance(methods, list) and "generateContent" not in methods:
            continue
        names.append(name.split("/", 1)[1])
    return names


def _select_fallback_model(api_key: str, tried: set[str]) -> str | None:
    preferred = (
        "gemini-flash-latest",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
    )
    models = _list_gemini_models(api_key)
    if not models:
        return None
    for name in preferred:
        if name in models and f"gemini/{name}" not in tried:
            return f"gemini/{name}"
    for name in models:
        candidate = f"gemini/{name}"
        if candidate not in tried:
            return candidate
    return None


def ask_gemini(prompt: str, model: str = "gemini/gemini-flash-latest") -> str:
    _require_litellm()
    load_dotenv("../../.env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "Missing GEMINI_API_KEY env var for Gemini. "
            "Export GEMINI_API_KEY=... before running."
        )

    requested = os.getenv("GEMINI_MODEL", model)
    fallback_models = [
        requested,
        model,
        "gemini/gemini-2.0-flash",
        "gemini/gemini-1.5-pro",
        "gemini/gemini-1.0-pro",
    ]
    seen = set()
    models_to_try = []
    for item in fallback_models:
        if item and item not in seen:
            seen.add(item)
            models_to_try.append(item)

    last_error: Exception | None = None
    for model_name in models_to_try:
        try:
            response = completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            break
        except Exception as exc:
            if _is_not_found_error(exc):
                last_error = exc
                continue
            raise
    else:
        selected = _select_fallback_model(api_key, set(models_to_try))
        if selected:
            response = completion(
                model=selected,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
        else:
            raise LookupError(
                "Gemini model not found. Set GEMINI_MODEL in .env "
                "to a valid model name."
            )
    try:
        return response.choices[0].message["content"].strip()
    except (AttributeError, KeyError, IndexError):
        return str(response)


def build_isin_market_cap_exchange_inception_question(ticker: str) -> str:
    return (
        "Return a JSON object with keys: isin, cap(Large-Cap, Mid-Cap, Small-Cap, Micro-Cap), market_cap_type(Mega-Cap, Large-Cap, Mid-Cap, Small-Cap, Micro-Cap), exchange, "
        "inception_date, company_name, delisted_date, sector, industry, etf (true or false), status (example Listed, Delisted etc). Use exchange only as NYSE or NASDAQ. "
        "Use DD-MMM-YYYY as dates format. If a value is "
        f"unknown, use null. Recheck ISIN from multiple sources including tradingview.com.  Target company ticker: {ticker}."
    )


def _question_builders() -> dict[str, Callable[[str], str]]:
    return {
        "isin": build_isin_market_cap_exchange_inception_question,
    }

def query_llm(question_type: str, arg1: str) -> str:
    if question_type not in _question_builders():
        raise ValueError(f"Unknown question type: {question_type}")
    if question_type == "isin":
        arg1 = arg1.upper()
    prompt = _question_builders()[question_type](arg1)
    return ask_gemini(prompt)

def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(
            "Usage: python use_llm.py <ticker> <question_type>\n"
            "question_type options: isin"
        )
        return 2

    ticker = argv[1].upper()
    question_type = argv[2].lower()
    builder = _question_builders().get(question_type)
    if builder is None:
        print(f"Unknown question_type: {question_type}")
        return 2

    prompt = builder(ticker)
    try:
        answer = ask_gemini(prompt)
        print(answer)
        return 0
    except Exception as exc:
        print(f"Error querying Gemini: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
