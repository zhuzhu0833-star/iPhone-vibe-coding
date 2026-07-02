"""Bilingual summarization via LLM APIs (China-accessible providers)."""

from __future__ import annotations

import json
import logging
import os
import re

import requests

from src.digest_slot import resolve_digest_slot
from src.models import DigestItem

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 45

PROVIDERS: dict[str, dict[str, str]] = {
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat",
        "env_keys": ("LLM_API_KEY", "DEEPSEEK_API_KEY"),
    },
    "qwen": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-turbo",
        "env_keys": ("LLM_API_KEY", "DASHSCOPE_API_KEY"),
    },
    "zhipu": {
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-4-flash",
        "env_keys": ("LLM_API_KEY", "ZHIPU_API_KEY"),
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "env_keys": ("LLM_API_KEY", "GROQ_API_KEY"),
    },
}


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def _fallback_zh(title: str) -> str:
    return f"详情请参阅原文链接：{title}"


def _fallback_advice() -> str:
    return "请关注原文细则，并提醒在途学生核对材料与时间节点。"


def _build_prompt(item: DigestItem) -> str:
    slot = resolve_digest_slot()
    slot_hint = (
        "本期早报侧重：招生数据、政策动向、学费与录取趋势。"
        if slot == "morning"
        else "本期晚报侧重：申请截止日、签证与工签政策、材料与审理时效。"
    )
    return f"""你是中国留学顾问团队的日报助手。请用 JSON 总结以下英文新闻，输出简体中文。

标题: {item.title_en}
来源: {item.source_name}（{item.country_name}）
类别: {item.category}
原文摘要: {_strip_html(item.summary_en)[:800]}
编辑提示: {slot_hint}

只返回合法 JSON，不要其他文字：
{{"summary_zh":"2-3句中文，说明政策/招生变化及对国际生的影响","action_advice":"1句可执行建议，以「顾问建议：」开头，说明顾问应提醒学生/家长做什么"}}"""


def _parse_json_response(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON in LLM response")
    return json.loads(match.group())


def _chat_summarize(
    item: DigestItem, api_key: str, url: str, model: str
) -> DigestItem:
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": _build_prompt(item)}],
            "temperature": 0.2,
            "max_tokens": 600,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]
    data = _parse_json_response(text)
    item.summary_zh = data.get("summary_zh", _fallback_zh(item.title_en))[:500]
    advice = data.get("action_advice", _fallback_advice())[:200]
    if not advice.startswith("顾问建议"):
        advice = f"顾问建议：{advice.lstrip('：:')}"
    item.action_advice = advice
    return item


def _resolve_api_key(provider: str) -> str | None:
    config = PROVIDERS.get(provider, PROVIDERS["deepseek"])
    for key_name in config["env_keys"]:
        value = os.environ.get(key_name, "").strip()
        if value:
            return value
    return None


def summarize_items(items: list[DigestItem]) -> list[DigestItem]:
    provider = os.environ.get("LLM_PROVIDER", "deepseek").lower()
    if provider not in PROVIDERS:
        logger.warning("Unknown LLM_PROVIDER %s, falling back to deepseek", provider)
        provider = "deepseek"

    api_key = _resolve_api_key(provider)
    if not api_key:
        logger.warning("No LLM API key; using title-only fallback")
        for item in items:
            if not item.summary_zh:
                item.summary_zh = _fallback_zh(item.title_en)
            if not item.action_advice:
                item.action_advice = _fallback_advice()
        return items

    config = PROVIDERS[provider]
    summarized: list[DigestItem] = []
    for item in items:
        try:
            summarized.append(
                _chat_summarize(item, api_key, config["url"], config["model"])
            )
        except Exception as exc:
            err = str(exc)
            if "402" in err or "Payment Required" in err:
                logger.warning(
                    "LLM API balance exhausted (402). Recharge DeepSeek or switch LLM_PROVIDER to qwen."
                )
            else:
                logger.warning("LLM summarize failed for %s: %s", item.link, exc)
            if not item.summary_zh:
                item.summary_zh = _fallback_zh(item.title_en)
            if not item.action_advice:
                item.action_advice = _fallback_advice()
            summarized.append(item)

    return summarized
