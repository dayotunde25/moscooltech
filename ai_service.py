"""AI content generation for the admin studio.

Provider-agnostic and SDK-free (uses `requests`, already a dependency):
  - gemini            -> Google Gemini generateContent API
  - openai_compatible -> any OpenAI-style /chat/completions endpoint (Groq,
                         OpenRouter, Together, a local server, ...)

Configuration (environment variables):
  AI_PROVIDER      gemini (default) | openai_compatible
  AI_API_KEY       provider key (required; absent -> feature disabled)
  AI_MODEL         model id (default gemini-2.5-flash)
  AI_BASE_URL      base URL for openai_compatible (default Groq)
  AI_TIMEOUT       request timeout seconds (default 90)

Only admin users can reach the routes that call this module, and generated
content is always escaped by the article.html renderer, so model output can
never inject HTML into a page.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/models'
GROQ_BASE = 'https://api.groq.com/openai/v1'
DEFAULT_MODEL = 'gemini-2.5-flash'

SYSTEM_PROMPT = """You are a senior technical writer for Moscool Technical Services, \
a Nigerian HVAC, refrigeration, solar/inverter and electrical company. The workshop is at \
16, Oredegbe Street, Off Ogundele Street, Agbado Station, Ifo LGA, Ogun State; the team \
serves Lagos Mainland (Ikeja, Yaba, Surulere, Maryland, Gbagada, Ogba) and Ogun State \
(Agbado, Ifo, Magboro, Mowe, Ibafo, Arepo).

Write practical, specific, locally accurate content for Nigerian homeowners and small \
businesses. Use realistic 2026 Naira price ranges only where they are defensible:
AC service 10,000-25,000; refrigerant recharge 25,000-60,000; capacitor 10,000-25,000;
compressor 120,000-350,000; split installation 40,000-90,000; solar packages roughly \
1.2m-6.5m depending on size. Never invent certifications, awards, customer counts, \
guarantees, statistics, or brand partnerships. Do not claim same-day service outside \
Lagos Mainland and Ogun State. Write in British/Nigerian English, plain and concrete, \
no marketing fluff, no emojis.

The phone number is +2349033150460. Mention it once, naturally, near the end."""

OUTPUT_RULES = """Return ONE JSON object and nothing else, with exactly these keys:
{
  "title": "50-65 characters, includes the target keyword, no site name",
  "meta_description": "140-155 characters, includes the keyword and a benefit",
  "content": "The article body. Use '## ' for H2 headings, '### ' for H3, '- ' for \
bullet lists and blank lines between paragraphs. Markdown bold (**text**) is allowed. \
No HTML tags. 900-1600 words unless asked otherwise.",
  "faqs": [{"q": "question", "a": "answer, 2-4 sentences"}],
  "suggested_image_alt": "short descriptive alt text"
}"""


class AiError(Exception):
    """A user-safe failure (message is shown to the admin)."""


def get_settings() -> dict[str, Any]:
    provider = (os.getenv('AI_PROVIDER') or 'gemini').strip().lower()
    if provider not in ('gemini', 'openai_compatible'):
        provider = 'gemini'
    return {
        'provider': provider,
        'api_key': (os.getenv('AI_API_KEY') or '').strip(),
        'model': (os.getenv('AI_MODEL') or '').strip() or DEFAULT_MODEL,
        'base_url': (os.getenv('AI_BASE_URL') or GROQ_BASE).rstrip('/'),
        # Keep below the 120s gunicorn timeout so a slow provider returns a
        # clean error instead of a 502 from the worker being killed.
        'timeout': _int_env('AI_TIMEOUT', 90, minimum=10, maximum=110),
    }


def _int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, value))


def is_configured() -> bool:
    return bool(get_settings()['api_key'])


def generate_article(topic: str, keyword: str = '', category: str = 'guides',
                     tone: str = 'practical', target_words: int = 1200,
                     faq_count: int = 4) -> dict[str, Any]:
    """Generate one article. Raises AiError with a safe message on failure."""
    topic = (topic or '').strip()
    if not topic:
        raise AiError('Enter a topic before generating.')
    keyword = (keyword or topic).strip()
    target_words = max(600, min(2000, int(target_words or 1200)))
    faq_count = max(0, min(6, int(faq_count or 0)))

    prompt = (
        f'{SYSTEM_PROMPT}\n\n'
        f'Topic: {topic}\n'
        f'Primary keyword: {keyword}\n'
        f'Category: {category}\n'
        f'Tone: {tone}\n'
        f'Target length: about {target_words} words.\n'
        f'Include {faq_count} frequently asked questions with direct answers.\n'
        f'Internal linking: mention the guides hub at /guides once if natural.\n\n'
        f'{OUTPUT_RULES}'
    )

    settings = get_settings()
    if not settings['api_key']:
        raise AiError('AI is not configured. Set AI_API_KEY (and optionally AI_MODEL) in the environment.')

    if settings['provider'] == 'gemini':
        raw = _call_gemini(prompt, settings)
    else:
        raw = _call_openai_compatible(prompt, settings)

    payload = _extract_json(raw)
    return _validate(payload, faq_count)


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
def _call_gemini(prompt: str, settings: dict[str, Any]) -> str:
    url = f"{GEMINI_BASE}/{settings['model']}:generateContent"
    body = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 8192,
            'responseMimeType': 'application/json',
        },
    }
    try:
        resp = requests.post(url, params={'key': settings['api_key']}, json=body,
                             timeout=settings['timeout'])
    except requests.exceptions.Timeout:
        raise AiError('The AI provider timed out. Try again, or reduce the target length.')
    except requests.exceptions.RequestException:
        raise AiError('Could not reach the AI provider. Check the server network connection.')

    data = _safe_json(resp)
    if resp.status_code != 200:
        message = _provider_message(data) or f'HTTP {resp.status_code}'
        raise AiError(f'AI provider error: {message}')

    candidates = data.get('candidates') or []
    if not candidates:
        blocked = (data.get('promptFeedback') or {}).get('blockReason')
        raise AiError(f'The model returned no content{f" ({blocked})" if blocked else ""}.')
    parts = ((candidates[0].get('content') or {}).get('parts') or [])
    text = ''.join(p.get('text', '') for p in parts if isinstance(p, dict))
    if not text.strip():
        raise AiError('The model returned an empty response. Try rephrasing the topic.')
    return text


def _call_openai_compatible(prompt: str, settings: dict[str, Any]) -> str:
    url = f"{settings['base_url']}/chat/completions"
    body = {
        'model': settings['model'],
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt.replace(SYSTEM_PROMPT, '').strip()},
        ],
        'temperature': 0.7,
        'max_tokens': 4096,
        'response_format': {'type': 'json_object'},
    }
    try:
        resp = requests.post(url, json=body, timeout=settings['timeout'],
                             headers={'Authorization': f"Bearer {settings['api_key']}"})
    except requests.exceptions.Timeout:
        raise AiError('The AI provider timed out. Try again, or reduce the target length.')
    except requests.exceptions.RequestException:
        raise AiError('Could not reach the AI provider. Check the server network connection.')

    data = _safe_json(resp)
    if resp.status_code != 200:
        message = _provider_message(data) or f'HTTP {resp.status_code}'
        raise AiError(f'AI provider error: {message}')

    choices = data.get('choices') or []
    if not choices:
        raise AiError('The model returned no content.')
    content = (choices[0].get('message') or {}).get('content') or ''
    if not content.strip():
        raise AiError('The model returned an empty response. Try rephrasing the topic.')
    return content


def _safe_json(resp: requests.Response) -> dict:
    try:
        data = resp.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _provider_message(data: dict) -> str:
    error = data.get('error')
    if isinstance(error, dict):
        return str(error.get('message') or error.get('status') or '')[:300]
    if isinstance(error, str):
        return error[:300]
    return ''


# ---------------------------------------------------------------------------
# Parsing / validation
# ---------------------------------------------------------------------------
def _extract_json(text: str) -> dict:
    """Accept a bare object, a ```json fenced block, or text around one."""
    cleaned = text.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    try:
        data = json.loads(cleaned)
    except ValueError:
        start, end = cleaned.find('{'), cleaned.rfind('}')
        if start == -1 or end <= start:
            raise AiError('The AI response was not valid JSON. Try again.')
        try:
            data = json.loads(cleaned[start:end + 1])
        except ValueError:
            raise AiError('The AI response was not valid JSON. Try again.')
    if not isinstance(data, dict):
        raise AiError('The AI response had an unexpected shape. Try again.')
    return data


def _validate(payload: dict, faq_count: int) -> dict[str, Any]:
    title = str(payload.get('title') or '').strip()
    content = str(payload.get('content') or '').strip()
    meta = str(payload.get('meta_description') or '').strip()
    alt = str(payload.get('suggested_image_alt') or '').strip()

    if len(title) < 10 or len(content) < 400:
        raise AiError('The AI returned incomplete content. Try again with a clearer topic.')

    faqs = []
    raw_faqs = payload.get('faqs')
    if isinstance(raw_faqs, list):
        for item in raw_faqs[:6]:
            if not isinstance(item, dict):
                continue
            q = str(item.get('q') or item.get('question') or '').strip()
            a = str(item.get('a') or item.get('answer') or '').strip()
            if q and a:
                faqs.append({'q': q[:300], 'a': a})

    if faq_count and not faqs:
        # The article is still usable without FAQs; the admin can add them.
        faqs = []

    return {
        'title': title[:200],
        'meta_description': (meta or content[:160])[:160],
        'content': content[:20000],
        'faqs': faqs,
        'suggested_image_alt': alt[:200],
    }
