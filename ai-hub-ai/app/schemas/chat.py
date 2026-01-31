"""智能客服问答相关 DTO"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求"""
    question: str
    device_id: Optional[str] = None
    tenant_id: Optional[str] = None
    # 审计相关：会话 ID（首次不传则自动创建，后续消息带上）
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    channel: str = "web"


class ChatResponse(BaseModel):
    """聊天响应"""
    issue_category: str
    alarm_code: Optional[str] = None
    confidence: float
    top_causes: List[str]
    steps: List[Dict[str, Any]]
    solution: Dict[str, str]
    safety_tip: str
    cited_docs: List[Dict[str, Any]]
    should_escalate: bool
    short_answer_text: str
    related_articles: Optional[List[Dict[str, Any]]] = None
    # 回复展示模式：conversation=仅展示对话气泡，不展示故障排查结构；未设置或 troubleshooting=按完整结构展示
    reply_mode: Optional[str] = None
    # 审计相关：返回给前端用于后续消息
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
