from pathlib import Path

import yaml
from pydantic import BaseModel, Field, TypeAdapter

DEFAULT_DATASET = Path(__file__).with_name("dataset.yaml")


class EvalCase(BaseModel):
    id: str
    category: str
    question: str
    reference_sql: str
    key_columns: list[int] = Field(default_factory=lambda: [0])
    value_columns: list[int] = Field(default_factory=list)
    ordered: bool = True
    min_overlap: float = Field(default=1.0, ge=0, le=1)
    value_tolerance: float = Field(default=0.01, ge=0)


CASES = TypeAdapter(list[EvalCase])


def load_cases(path: Path = DEFAULT_DATASET) -> list[EvalCase]:
    return CASES.validate_python(yaml.safe_load(path.read_text(encoding="utf-8")))
