import hashlib
import sqlite3
from collections.abc import Collection
from functools import cached_property

from cinerocket.database.connection import ReadOnlyDatabase
from cinerocket.domain.errors import QueryExecutionError
from cinerocket.domain.models import CellValue, ColumnInfo, ForeignKeyInfo, TableInfo

PREVIEW_TEXT_LENGTH = 120


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def shorten(value: CellValue) -> CellValue:
    if isinstance(value, str) and len(value) > PREVIEW_TEXT_LENGTH:
        return value[:PREVIEW_TEXT_LENGTH] + "…"
    return value


class SchemaCatalog:
    def __init__(self, database: ReadOnlyDatabase, excluded_tables: Collection[str] = ()) -> None:
        self._database = database
        self._excluded = {name.lower() for name in excluded_tables}

    @cached_property
    def tables(self) -> dict[str, TableInfo]:
        with self._database.connect() as connection:
            names = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
                    "ORDER BY name"
                )
                if row[0].lower() not in self._excluded
            ]
            return {name: self._load_table(connection, name) for name in names}

    @cached_property
    def fingerprint(self) -> str:
        payload = "|".join(table.model_dump_json() for table in self.tables.values())
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    @property
    def table_names(self) -> list[str]:
        return list(self.tables)

    def resolve_table(self, name: str) -> TableInfo:
        for table_name, table in self.tables.items():
            if table_name.lower() == name.strip().lower():
                return table
        raise QueryExecutionError(
            f"Tabela '{name}' não existe. Tabelas disponíveis: {', '.join(self.table_names)}."
        )

    def resolve_column(self, table: TableInfo, name: str) -> str:
        for column in table.column_names:
            if column.lower() == name.strip().lower():
                return column
        raise QueryExecutionError(
            f"Coluna '{name}' não existe em {table.name}. Colunas: {', '.join(table.column_names)}."
        )

    def describe(self) -> str:
        return "\n".join(self._describe_table(table) for table in self.tables.values())

    def sample_rows(self, table_name: str, limit: int = 3) -> tuple[list[str], list[list[CellValue]]]:
        table = self.resolve_table(table_name)
        with self._database.connect() as connection:
            cursor = connection.execute(f"SELECT * FROM {quote_identifier(table.name)} LIMIT ?", (limit,))
            columns = [description[0] for description in cursor.description]
            rows = [[shorten(value) for value in row] for row in cursor.fetchall()]
        return columns, rows

    def distinct_values(self, table_name: str, column_name: str, limit: int = 20) -> list[CellValue]:
        table = self.resolve_table(table_name)
        column = quote_identifier(self.resolve_column(table, column_name))
        with self._database.connect() as connection:
            cursor = connection.execute(
                f"SELECT {column}, COUNT(*) AS frequency FROM {quote_identifier(table.name)} "
                f"WHERE {column} IS NOT NULL GROUP BY {column} ORDER BY frequency DESC LIMIT ?",
                (limit,),
            )
            return [shorten(row[0]) for row in cursor.fetchall()]

    @staticmethod
    def _load_table(connection: sqlite3.Connection, name: str) -> TableInfo:
        quoted = quote_identifier(name)
        columns = [
            ColumnInfo(name=row[1], type=row[2] or "ANY", nullable=not row[3], primary_key=bool(row[5]))
            for row in connection.execute(f"PRAGMA table_info({quoted})")
        ]
        foreign_keys = [
            ForeignKeyInfo(column=row[3], references_table=row[2], references_column=row[4])
            for row in connection.execute(f"PRAGMA foreign_key_list({quoted})")
        ]
        row_count = connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
        return TableInfo(name=name, columns=columns, foreign_keys=foreign_keys, row_count=row_count)

    @staticmethod
    def _describe_table(table: TableInfo) -> str:
        columns = ", ".join(
            f"{column.name} {column.type}{' PK' if column.primary_key else ''}"
            f"{'' if column.nullable or column.primary_key else ' NOT NULL'}"
            for column in table.columns
        )
        references = "".join(
            f"\n  FK {fk.column} -> {fk.references_table}.{fk.references_column}" for fk in table.foreign_keys
        )
        return f"{table.name} ({table.row_count} linhas): {columns}{references}"
