if __name__ == "__main__":
    import os
    import uvicorn
    from app.core.config import settings
    port = int(os.getenv("PORT", str(settings.PORT)))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
