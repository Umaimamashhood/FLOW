"""Runtime configuration. Environment variables override the defaults."""
import os
from pathlib import Path

OLLAMA_URL = os.getenv("FLOW_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("FLOW_OLLAMA_MODEL", "qwen2.5-coder:7b")
MOCK_MODE = os.getenv("FLOW_MOCK", "0") == "1"  # stubs the LLM, voice and desktop control

DATA_DIR = Path(os.getenv("FLOW_DATA", Path.home() / ".flow"))
DB_PATH = Path(os.getenv("FLOW_DB", DATA_DIR / "flow.db"))
PROJECTS_DIR = Path(os.getenv("FLOW_PROJECTS", Path.home() / "Desktop"))
ALLOWED_DIRS = [PROJECTS_DIR, Path.home() / "Documents", Path.home() / "Desktop"]

MAX_SUBTASKS = 10          # SRS A.2
LLM_RETRY_COUNT = 3        # SRS 4.3.1
LLM_RETRY_DELAY = 2        # seconds
APP_LAUNCH_TIMEOUT = 10    # seconds (SRS A.2)
RUN_TIMEOUT = 30           # seconds, generated programs (FR-21)
ASR_CONFIDENCE_MIN = 0.50  # SRS A.2 (FR-4)
WHISPER_MODEL = os.getenv("FLOW_WHISPER_MODEL", "base.en")
