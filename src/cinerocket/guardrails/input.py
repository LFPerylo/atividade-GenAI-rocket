import re
import unicodedata

from cinerocket.domain.errors import InvalidQuestionError

WHITESPACE = re.compile(r"\s+")


class QuestionGuard:
    def __init__(self, max_length: int) -> None:
        self._max_length = max_length

    def clean(self, question: str) -> str:
        printable = "".join(
            char for char in question if char.isspace() or unicodedata.category(char)[0] != "C"
        )
        cleaned = WHITESPACE.sub(" ", printable).strip()
        if not cleaned:
            raise InvalidQuestionError("A pergunta não pode ser vazia.")
        if len(cleaned) > self._max_length:
            raise InvalidQuestionError(f"A pergunta excede o limite de {self._max_length} caracteres.")
        return cleaned
