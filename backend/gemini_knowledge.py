#!/usr/bin/env python3
"""
Gemini knowledge helper for strategic guidance.
"""

import google.generativeai as genai


def ask_gemini(api_key: str, model_name: str, prompt: str) -> str:
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY nao configurada.")

    genai.configure(api_key=api_key)

    fallback_models = [
        model_name,
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
    ]
    tried = []
    last_exception = None

    for candidate in fallback_models:
        if candidate in tried:
            continue
        tried.append(candidate)
        try:
            model = genai.GenerativeModel(model_name=candidate)
            response = model.generate_content(prompt)
            if response and getattr(response, "text", None):
                return response.text
        except Exception as exc:
            last_exception = exc
            error_text = str(exc).lower()
            if any(token in error_text for token in ["429", "quota", "rate limit", "resource exhausted", "not found", "not supported"]):
                continue
            raise

    if last_exception:
        raise RuntimeError(f"Falha Gemini em todos os modelos tentados {tried}: {last_exception}")
    return "Sem resposta da Gemini."
