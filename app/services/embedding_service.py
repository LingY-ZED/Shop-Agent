"""向量嵌入服务 - 使用 OpenAI 兼容 API (SiliconFlow)"""

import logging
from typing import List
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """向量嵌入服务，使用 SiliconFlow Embeddings (OpenAI 兼容)"""

    def __init__(self, model: str = "BAAI/bge-large-zh-v1.5"):
        """
        初始化嵌入服务

        Args:
            model: 嵌入模型名称
        """
        self.client = AsyncOpenAI(
            api_key=settings.siliconflow_api_key,
            base_url="https://api.siliconflow.cn/v1",
        )
        self.model = model

    async def embed_text(self, text: str) -> List[float]:
        """
        将单个文本转换为向量

        Args:
            text: 输入文本

        Returns:
            向量列表
        """
        try:
            response = await self.client.embeddings.create(model=self.model, input=text)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"生成嵌入失败: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为向量

        Args:
            texts: 输入文本列表

        Returns:
            向量列表的列表
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model, input=texts
            )
            # 按输入顺序返回 embeddings
            embeddings = sorted(response.data, key=lambda x: x.index)
            return [e.embedding for e in embeddings]
        except Exception as e:
            logger.error(f"批量生成嵌入失败: {e}")
            raise


# 全局实例
embedding_service = EmbeddingService()
