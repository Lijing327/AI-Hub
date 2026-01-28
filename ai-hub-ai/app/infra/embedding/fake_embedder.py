"""本地伪向量：用于先把链路跑通（不依赖外部模型）"""
import hashlib
from app.infra.embedding.base import IEmbedder


class FakeEmbedder(IEmbedder):
    """
    本地伪向量：用于先把链路跑通（不依赖外部模型）
    向量维度固定 64
    """
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            # 取前 64 个字节（不够就循环），映射到 [0,1]
            v = [(h[i % len(h)] / 255.0) for i in range(64)]
            vectors.append(v)
        return vectors
