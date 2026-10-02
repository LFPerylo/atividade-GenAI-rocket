import logging
import os

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(level: str) -> None:
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    logging.basicConfig(level=level.upper(), format=LOG_FORMAT, force=True)
    for noisy in ("httpx", "httpcore", "google_genai.models"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
