from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.api.models import ChatRequest, ChatResponse
from app.services.llm_service import llm_service
from app.agents.order_agent import order_agent
from app.agents.rag_agent import rag_agent
from app.agents.router_agent import router_agent

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天端点

    处理用户对话请求，调用大模型生成回复。
    """
    try:
        # 构建消息列表
        messages = []

        # 添加系统提示词（如果提供）
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })

        # 添加用户消息
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # 调用大模型
        response = await llm_service.chat_completion(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        return ChatResponse(
            content=response["content"],
            role=response["role"],
            finish_reason=response.get("finish_reason"),
            usage=response.get("usage")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天服务错误: {str(e)}")


@router.post("/chat/order", response_model=ChatResponse)
async def chat_order(request: ChatRequest):
    """
    订单查询聊天端点

    处理用户订单相关对话请求，使用Tool Calling自动查询订单状态。
    支持：订单号查询、快递单号查询、商品名称搜索、用户订单历史查询。
    """
    try:
        # 获取最后一条用户消息
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break

        if not user_message:
            raise HTTPException(status_code=400, detail="未找到用户消息")

        # 构建对话历史（用于多轮对话）
        history = []
        for msg in request.messages[:-1]:
            if msg.role in ["user", "assistant"]:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # 调用OrderAgent处理
        result = await order_agent.process(user_message, history)

        return ChatResponse(
            content=result["content"],
            role="assistant",
            finish_reason="stop",
            tool_used=result.get("tool_used", False),
            tool_name=result.get("tool_name")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"订单查询服务错误: {str(e)}")


@router.get("/chat/history")
async def get_chat_history():
    """获取聊天历史（占位）"""
    return {"message": "聊天历史功能待实现"}


@router.post("/chat/auto", response_model=ChatResponse)
async def chat_auto(request: ChatRequest):
    """
    智能聊天端点（统一入口）

    自动识别用户意图并路由到相应的Agent：
    - 订单查询意图 -> OrderAgent
    - 产品推荐意图 -> RAGAgent
    - 其他 -> 基础对话
    """
    try:
        # 获取最后一条用户消息
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break

        if not user_message:
            raise HTTPException(status_code=400, detail="未找到用户消息")

        # 构建对话历史
        history = []
        for msg in request.messages[:-1]:
            if msg.role in ["user", "assistant"]:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # 调用Router Agent自动路由
        result = await router_agent.process(user_message, history)

        return ChatResponse(
            content=result["content"],
            role="assistant",
            finish_reason="stop",
            tool_used=result.get("tool_used", False),
            tool_name=result.get("tool_name"),
            intent=result.get("intent")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能聊天服务错误: {str(e)}")


@router.post("/chat/product", response_model=ChatResponse)
async def chat_product(request: ChatRequest):
    """
    产品推荐聊天端点

    处理用户产品相关对话请求，使用RAG检索相关产品并生成推荐。
    """
    try:
        # 获取最后一条用户消息
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break

        if not user_message:
            raise HTTPException(status_code=400, detail="未找到用户消息")

        # 构建对话历史
        history = []
        for msg in request.messages[:-1]:
            if msg.role in ["user", "assistant"]:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # 调用RAG Agent处理
        result = await rag_agent.process(user_message, history=history)

        return ChatResponse(
            content=result["content"],
            role="assistant",
            finish_reason="stop",
            tool_used=result.get("tool_used", False),
            tool_name=result.get("tool_name")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"产品推荐服务错误: {str(e)}")
