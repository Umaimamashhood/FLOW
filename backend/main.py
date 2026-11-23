"""Start the FLOW backend: python main.py (serves http://127.0.0.1:8765)."""
import uvicorn


def main() -> None:
    uvicorn.run("server:app", host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
