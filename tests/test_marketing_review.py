"""Tests for shared marketing output review helpers."""

import json
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_review_marketing_output_skips_without_api_key():
    from opencmo.marketing_review import review_marketing_output

    with patch("opencmo.marketing_review.llm.get_key_async", AsyncMock(return_value=None)):
        result = await review_marketing_output(
            agent_name="CMO Agent",
            user_message="Help me write positioning",
            output_text="Original output",
        )

    assert result == "Original output"


@pytest.mark.asyncio
async def test_review_marketing_output_rewrites_for_supported_agent():
    from opencmo.marketing_review import review_marketing_output

    with patch("opencmo.marketing_review.llm.get_key_async", AsyncMock(return_value="sk-test")), \
         patch("opencmo.marketing_review.llm.chat_completion", AsyncMock(return_value="Rewritten output")):
        result = await review_marketing_output(
            agent_name="CMO Agent",
            user_message="Help me write positioning",
            output_text="Original output with a longer draft that explains the product, the audience, and the value proposition.",
        )

    assert result == "Rewritten output"


def test_marketing_review_profile_selection():
    from opencmo.marketing_review import get_marketing_review_profile

    assert get_marketing_review_profile("Reddit Expert") == "community_social"
    assert get_marketing_review_profile("Twitter Expert") == "timeline_native"
    assert get_marketing_review_profile("LinkedIn Expert") == "professional_social"
    assert get_marketing_review_profile("V2EX Expert") == "developer_forum"
    assert get_marketing_review_profile("Jike Expert") == "maker_feed"
    assert get_marketing_review_profile("Xiaohongshu Expert") == "experience_note"
    assert get_marketing_review_profile("Devto Expert") == "hands_on_longform"
    assert get_marketing_review_profile("Ruanyifeng Weekly Expert") == "submission_ready"
    assert get_marketing_review_profile("SEO Audit Expert") == "seo_growth"
    assert get_marketing_review_profile("CMO Agent") == "strategic_marketing"


@pytest.mark.asyncio
async def test_review_marketing_output_with_metadata_returns_tags():
    from opencmo.marketing_review import review_marketing_output_with_metadata

    llm_payload = {
        "revised_output": "Reviewed output",
        "weak_points": ["proof", "next_move"],
    }
    with patch("opencmo.marketing_review.llm.get_key_async", AsyncMock(return_value="sk-test")), \
         patch("opencmo.marketing_review.llm.chat_completion", AsyncMock(return_value=json.dumps(llm_payload))):
        result = await review_marketing_output_with_metadata(
            agent_name="LinkedIn Expert",
            user_message="Rewrite this post",
            output_text="Original draft with enough content for review to run safely.",
        )

    assert result["final_output"] == "Reviewed output"
    assert result["review_applied"] is True
    assert result["profile"] == "professional_social"
    assert result["weak_points"] == ["proof", "next_move"]


@pytest.mark.asyncio
async def test_review_marketing_output_unwraps_nested_json_string():
    from opencmo.marketing_review import review_marketing_output_with_metadata

    llm_payload = {
        "revised_output": json.dumps(
            {
                "revised_output": "动态文案\n这是即刻正文",
                "weak_points": ["proof"],
            },
            ensure_ascii=False,
        ),
        "weak_points": ["clarity"],
    }
    with patch("opencmo.marketing_review.llm.get_key_async", AsyncMock(return_value="sk-test")), \
         patch("opencmo.marketing_review.llm.chat_completion", AsyncMock(return_value=json.dumps(llm_payload, ensure_ascii=False))):
        result = await review_marketing_output_with_metadata(
            agent_name="Jike Expert",
            user_message="帮我写一条即刻动态",
            output_text="原始草稿，长度足够触发 review。这里补一段额外说明，确保超过 review 的最小长度阈值。",
        )

    assert result["final_output"] == "动态文案\n这是即刻正文"
    assert result["review_applied"] is True
    assert result["profile"] == "maker_feed"


@pytest.mark.asyncio
async def test_review_marketing_output_unwraps_malformed_nested_json_string():
    from opencmo.marketing_review import review_marketing_output_with_metadata

    malformed_nested = '{"revised_output":"节点\\n/go/openai\\n\\n标题\\n[开源] OpenCMO","weak_points":["priority","next_"}'
    llm_payload = {
        "revised_output": malformed_nested,
        "weak_points": ["clarity"],
    }
    with patch("opencmo.marketing_review.llm.get_key_async", AsyncMock(return_value="sk-test")), \
         patch("opencmo.marketing_review.llm.chat_completion", AsyncMock(return_value=json.dumps(llm_payload, ensure_ascii=False))):
        result = await review_marketing_output_with_metadata(
            agent_name="V2EX Expert",
            user_message="帮我写一篇 V2EX 帖子",
            output_text="原始草稿，长度足够触发 review。这里补一段额外说明，确保超过 review 的最小长度阈值。",
        )

    assert result["final_output"] == "节点\n/go/openai\n\n标题\n[开源] OpenCMO"
    assert result["review_applied"] is True
    assert result["profile"] == "developer_forum"
