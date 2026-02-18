#!/usr/bin/env python3
"""
Gemini knowledge helper for strategic guidance.
"""

import google.generativeai as genai


def ask_gemini(api_key: str, model_name: str, prompt: str) -> str:
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY nao configurada.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=model_name)

    response = model.generate_content(prompt)
    if not response or not getattr(response, "text", None):
        return "Sem resposta da Gemini."

    return response.text
