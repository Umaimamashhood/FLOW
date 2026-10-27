"""Entry point: python -m flow  (also used by the packaged backend executable)."""
import uvicorn


def main() -> None:
    uvicorn.run("flow.server:app", host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
