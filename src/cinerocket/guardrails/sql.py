from collections.abc import Callable, Iterable

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from cinerocket.domain.errors import UnsafeQueryError

FORBIDDEN_NODES: tuple[type[exp.Expr], ...] = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.TruncateTable,
    exp.Pragma,
    exp.Attach,
    exp.Detach,
    exp.Command,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
)

FORBIDDEN_FUNCTIONS = frozenset({"load_extension", "readfile", "writefile", "edit", "fts3_tokenizer"})


class SqlGuard:
    def __init__(self, allowed_tables: Callable[[], Iterable[str]], dialect: str = "sqlite") -> None:
        self._allowed_tables = allowed_tables
        self._dialect = dialect

    def validate(self, sql: str) -> str:
        statement = sql.strip().rstrip(";").strip()
        if not statement:
            raise UnsafeQueryError("A consulta SQL está vazia.")
        tree = self._parse_single(statement)
        if not isinstance(tree, exp.Query):
            raise UnsafeQueryError("Apenas consultas de leitura (SELECT/WITH) são permitidas.")
        forbidden = next((node for node in tree.walk() if isinstance(node, FORBIDDEN_NODES)), None)
        if forbidden is not None:
            raise UnsafeQueryError(f"Operação não permitida na consulta: {forbidden.key.upper()}.")
        self._check_functions(tree)
        self._check_tables(tree)
        return statement

    def _parse_single(self, statement: str) -> exp.Expr:
        try:
            trees = [tree for tree in sqlglot.parse(statement, read=self._dialect) if tree is not None]
        except ParseError as error:
            raise UnsafeQueryError(f"SQL inválido: {error}") from error
        if len(trees) != 1:
            raise UnsafeQueryError("Envie exatamente uma consulta SQL por vez.")
        return trees[0]

    @staticmethod
    def _check_functions(tree: exp.Expr) -> None:
        for function in tree.find_all(exp.Func):
            if function.name.lower() in FORBIDDEN_FUNCTIONS:
                raise UnsafeQueryError(f"Função não permitida na consulta: {function.name}.")

    def _check_tables(self, tree: exp.Expr) -> None:
        cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
        referenced = {table.name.lower() for table in tree.find_all(exp.Table)}
        if "" in referenced:
            raise UnsafeQueryError("Funções de tabela não são permitidas; use apenas as tabelas do catálogo.")
        allowed = {name.lower() for name in self._allowed_tables()}
        unknown = sorted(referenced - cte_names - allowed)
        if unknown:
            raise UnsafeQueryError(
                f"Tabela(s) não permitida(s): {', '.join(unknown)}. Use apenas: {', '.join(sorted(allowed))}."
            )
