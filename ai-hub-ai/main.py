"""
入口已迁移至 app.main，业务逻辑均在 app/ 目录下。
请使用: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
或执行: python main.py（将启动 uvicorn 并加载 app.main:app）
"""
if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
