"""历史摘要服务：使用LLM对旧对话进行压缩。"""

import logging
from typing import Any, Dict, List, Optional

from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


SUMMARY_SYSTEM_PROMPT = """你是电商客服系统的对话记忆压缩器。
请将较早历史对话压缩为一段不超过120字的摘要，必须保留：
1) 用户查询过的订单号/物流线索与状态
2) 用户咨询过的商品类型与偏好
3) 预算、用途等限制条件

要求：
- 只保留事实，不要编造
- 使用简体中文
- 输出一段连续文本，不要Markdown列表
"""


class SummaryService:
    """基于LLM的历史摘要服务。"""

    async def summarize_history(
        self,
        old_turns: List[Dict[str, Any]],
        previous_summary: Optional[str] = None,
    ) -> str:
        """将旧对话压缩成摘要文本。"""
        if not old_turns:
            return previous_summary or ""

        dialog_lines = []
        for turn in old_turns:
            role = turn.get("role", "user")
            content = (turn.get("content") or "").strip()
            if not content:
                continue
            dialog_lines.append(f"{role}: {content}")

        if not dialog_lines:
            return previous_summary or ""

        user_prompt = (
            f"已有摘要（可为空）：{previous_summary or '无'}\n\n"
            f"待压缩历史：\n" + "\n".join(dialog_lines)
        )

        try:
            response = await llm_service.generate_response(
                prompt=user_prompt,
                system_prompt=SUMMARY_SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=220,
            )
            summary = (response or "").strip()
            if summary:
                return summary
        except Exception as exc:
            logger.warning(f"LLM摘要生成失败，使用规则回退: {exc}")

        # 回退策略：拼接最近若干条历史
        fallback_chunks = []
        for line in dialog_lines[-4:]:
            fallback_chunks.append(line[:30])
        fallback_text = "；".join(fallback_chunks)
        if previous_summary:
            return f"{previous_summary}；{fallback_text}"[:160]
        return fallback_text[:160]


summary_service = SummaryService()
