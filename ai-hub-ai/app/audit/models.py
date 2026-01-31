"""审计日志数据模型"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class StartConversationRequest(BaseModel):
    """创建会话请求"""
    tenant_id: str = "default"
    user_id: Optional[str] = None
    channel: str = "web"
    meta_json: Optional[str] = None


class StartConversationResponse(BaseModel):
    """创建会话响应"""
    conversationId: str  # UUID 字符串
    startedAt: datetime


class AppendMessageRequest(BaseModel):
    """追加消息请求"""
    conversationId: str
    role: str = "user"  # user/assistant/system
    content: str = ""
    isMasked: bool = False
    maskedContent: Optional[str] = None


class AppendMessageResponse(BaseModel):
    """追加消息响应"""
    messageId: str  # UUID 字符串
    createdAt: datetime


class LogDecisionRequest(BaseModel):
    """记录决策请求"""
    messageId: str
    intentType: str = "chat"
    confidence: float = 0.0
    modelName: Optional[str] = None
    promptVersion: Optional[str] = None
    useKnowledge: bool = False
    fallbackReason: Optional[str] = None
    tokensIn: Optional[int] = None
    tokensOut: Optional[int] = None


class RetrievalDocItem(BaseModel):
    """RAG 命中文档项"""
    docId: str
    docTitle: Optional[str] = None
    score: float = 0.0
    rank: int = 0
    chunkId: Optional[str] = None


class LogRetrievalRequest(BaseModel):
    """记录 RAG 检索请求"""
    messageId: str
    docs: List[RetrievalDocItem] = []


class LogResponseRequest(BaseModel):
    """记录响应请求"""
    messageId: str
    finalAnswer: Optional[str] = None
    responseTimeMs: int = 0
    isSuccess: bool = True
    errorType: Optional[str] = None
    errorDetail: Optional[str] = None


class EndConversationRequest(BaseModel):
    """结束会话请求"""
    conversationId: str


class AuditOperationResponse(BaseModel):
    """通用操作响应"""
    success: bool = True
    message: Optional[str] = None
