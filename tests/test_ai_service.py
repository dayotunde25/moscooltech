"""Unit tests for ai_service (no network; requests.post is mocked)."""
import json as jsonlib

import pytest

import ai_service


VALID_PAYLOAD = {
    'title': 'Cold Room Setup Cost in Nigeria: 2026 Guide',
    'meta_description': 'What a small cold room costs to set up in Nigeria in 2026, '
                        'including panels, condensing unit and installation labour.',
    'content': '## What it costs\n\n' + ('Cold room detail. ' * 50),
    'faqs': [{'q': 'How much?', 'a': 'About N2m.'}],
    'suggested_image_alt': 'Cold room installation in Lagos',
}


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_extract_json_accepts_fenced_block():
    raw = '```json\n' + jsonlib.dumps(VALID_PAYLOAD) + '\n```'
    assert ai_service._extract_json(raw)['title'] == VALID_PAYLOAD['title']


def test_extract_json_accepts_surrounding_text():
    raw = 'Here you go:\n' + jsonlib.dumps(VALID_PAYLOAD) + '\nEnjoy.'
    assert ai_service._extract_json(raw)['title'] == VALID_PAYLOAD['title']


def test_extract_json_rejects_garbage():
    with pytest.raises(ai_service.AiError):
        ai_service._extract_json('no json here')


def test_validate_trims_meta_and_keeps_faqs():
    payload = dict(VALID_PAYLOAD)
    payload['meta_description'] = 'x' * 300
    result = ai_service._validate(payload, faq_count=2)
    assert len(result['meta_description']) <= 160
    assert result['faqs'][0]['q'] == 'How much?'


def test_generate_article_gemini(monkeypatch):
    monkeypatch.setenv('AI_API_KEY', 'test-key')
    monkeypatch.setenv('AI_PROVIDER', 'gemini')
    monkeypatch.setenv('AI_MODEL', 'gemini-test')
    calls = {}

    def fake_post(url, params=None, json=None, timeout=None):  # noqa: A002 - requests kwarg
        calls['url'] = url
        calls['params'] = params
        calls['body'] = json
        return _FakeResponse(200, {
            'candidates': [{'content': {'parts': [{'text': jsonlib.dumps(VALID_PAYLOAD)}]}}]
        })

    monkeypatch.setattr(ai_service.requests, 'post', fake_post)
    result = ai_service.generate_article('Cold room cost', 'cold room cost Nigeria', faq_count=1)

    assert result['title'] == VALID_PAYLOAD['title']
    assert result['faqs'][0]['a'] == 'About N2m.'
    assert ':generateContent' in calls['url']
    assert calls['params'] == {'key': 'test-key'}
    assert calls['body']['generationConfig']['responseMimeType'] == 'application/json'


def test_generate_article_openai_compatible(monkeypatch):
    monkeypatch.setenv('AI_API_KEY', 'test-key')
    monkeypatch.setenv('AI_PROVIDER', 'openai_compatible')
    monkeypatch.setenv('AI_BASE_URL', 'https://example.invalid/v1')
    monkeypatch.setenv('AI_MODEL', 'test-model')
    calls = {}

    def fake_post(url, json=None, timeout=None, headers=None):  # noqa: A002 - requests kwarg
        calls['url'] = url
        calls['headers'] = headers
        return _FakeResponse(200, {
            'choices': [{'message': {'content': jsonlib.dumps(VALID_PAYLOAD)}}]
        })

    monkeypatch.setattr(ai_service.requests, 'post', fake_post)
    result = ai_service.generate_article('Cold room cost', faq_count=1)

    assert result['title'] == VALID_PAYLOAD['title']
    assert calls['url'] == 'https://example.invalid/v1/chat/completions'
    assert calls['headers']['Authorization'] == 'Bearer test-key'


def test_generate_article_reports_provider_error(monkeypatch):
    monkeypatch.setenv('AI_API_KEY', 'test-key')
    monkeypatch.setenv('AI_PROVIDER', 'gemini')

    def fake_post(url, params=None, json=None, timeout=None):  # noqa: A002 - requests kwarg
        return _FakeResponse(429, {'error': {'message': 'Quota exceeded'}})

    monkeypatch.setattr(ai_service.requests, 'post', fake_post)
    with pytest.raises(ai_service.AiError) as excinfo:
        ai_service.generate_article('Any topic')
    assert 'Quota exceeded' in str(excinfo.value)


def test_generate_article_without_key(monkeypatch):
    monkeypatch.delenv('AI_API_KEY', raising=False)
    with pytest.raises(ai_service.AiError) as excinfo:
        ai_service.generate_article('Any topic')
    assert 'not configured' in str(excinfo.value).lower()
