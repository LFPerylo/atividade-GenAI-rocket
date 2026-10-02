import hashlib
import re
import unicodedata

NON_WORD = re.compile(r"[^\w%$]+")


def normalize_question(question: str) -> str:
    decomposed = unicodedata.normalize("NFKD", question.lower())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return NON_WORD.sub(" ", without_accents).strip()


def cache_key(question: str, *scopes: str) -> str:
    payload = "|".join((*scopes, normalize_question(question)))
    return hashlib.sha256(payload.encode()).hexdigest()
