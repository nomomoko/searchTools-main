from uvicorn import run

import app


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Start the FastAPI server with uvicorn"""
    run(app.app, host=host, port=port)


if __name__ == "__main__":
    import typer

    typer.run(start_server)
