from pydantic_ai import ModelRetry

from cinerocket.agent.deps import AgentDeps
from cinerocket.domain.errors import QueryExecutionError, UnsafeQueryError
from cinerocket.domain.models import AgentAnswer


def normalize_markdown(text: str) -> str:
    return text.replace("\\r\\n", "\n").replace("\\n", "\n").strip()


def validate_answer(deps: AgentDeps, answer: AgentAnswer) -> AgentAnswer:
    answer = answer.model_copy(update={"answer": normalize_markdown(answer.answer)})
    if not answer.answer:
        raise ModelRetry("O campo answer está vazio. Escreva a resposta ao usuário com base nos resultados.")
    if answer.out_of_scope:
        if deps.executed:
            raise ModelRetry(
                "Você consultou o catálogo, então a pergunta está no escopo: use out_of_scope=false "
                "e responda com o SQL final testado."
            )
        return answer.model_copy(update={"sql": None, "chart": None})
    if not answer.sql:
        raise ModelRetry("Informe em sql a consulta final, testada com run_sql, que sustenta a resposta.")
    if not deps.was_executed(answer.sql):
        raise ModelRetry(
            "O SQL final não foi executado com run_sql nesta análise. Execute-o com run_sql e escreva a "
            "resposta somente a partir do resultado retornado."
        )
    try:
        result = deps.execute(answer.sql)
    except (UnsafeQueryError, QueryExecutionError) as error:
        raise ModelRetry(f"O SQL final falhou: {error} Corrija e teste com run_sql.") from error
    if answer.chart and not {answer.chart.x, answer.chart.y} <= set(result.columns):
        return answer.model_copy(update={"chart": None})
    return answer
