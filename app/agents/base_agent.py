from typing import List, Dict, Any, Optional
from app.services.llm_service import llm_service


class BaseAgent:
    """基础Agent类"""

    def __init__(self):
        self.llm_service = llm_service

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """基础对话方法"""
        response = await self.llm_service.chat_completion(messages, **kwargs)
        return response

    async def chat_with_functions(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """带函数调用的对话"""
        response = await self.llm_service.chat_completion_with_functions(
            messages=messages,
            functions=functions,
            **kwargs
        )
        return response

    def build_messages(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return messages
