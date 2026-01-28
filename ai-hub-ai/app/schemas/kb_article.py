"""知识库条目 DTO，与 SQL Server kb_article 表对应"""
from pydantic import BaseModel


class KbArticle(BaseModel):
    id: int
    tenant_id: str
    title: str | None = None
    question_text: str | None = None
    cause_text: str | None = None
    solution_text: str | None = None
    tags: str | None = None  # 你表里如果是 json/text，这里先用 str
    status: str | None = None
    version: int | None = None

    class Config:
        from_attributes = True
