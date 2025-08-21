import sys
import os
# 添加 src 路径到搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from uvicorn import run
import app


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Start the FastAPI server with uvicorn"""
    run(app.app, host=host, port=port)


if __name__ == "__main__":
    import typer

    typer.run(start_server)
