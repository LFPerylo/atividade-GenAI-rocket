from cinerocket.container import Container
from cinerocket.domain.models import ChatResponse
from tests.conftest import ScriptedModel

QUESTION = "Quais filmes tiveram a maior receita?"


async def test_answer_rows_come_from_database(container: Container) -> None:
    response = await container.service.ask(QUESTION)

    assert response.result is not None
    assert response.result.rows == [["Barbie", 7000.0], ["Duna", 2000.0]]
    assert response.chart is not None
    assert response.cached is False
    assert container.service.transcript(response.session_id) == [response]


async def test_repeated_question_is_served_from_cache(
    container: Container, scripted_model: ScriptedModel
) -> None:
    first = await container.service.ask(QUESTION)
    calls_after_first = len(scripted_model.calls)

    second = await container.service.ask(f"  {QUESTION.upper()} ")

    assert second.cached is True
    assert second.session_id != first.session_id
    assert second.result == first.result
    assert len(scripted_model.calls) == calls_after_first


async def test_follow_up_receives_conversation_history(
    container: Container, scripted_model: ScriptedModel
) -> None:
    first: ChatResponse = await container.service.ask(QUESTION)

    await container.service.ask("E qual teve a menor?", session_id=first.session_id)

    follow_up_prompt = scripted_model.calls[-2]
    prompts = [
        part.content
        for message in follow_up_prompt
        for part in message.parts
        if part.part_kind == "user-prompt"
    ]
    assert prompts == [QUESTION, "E qual teve a menor?"]
