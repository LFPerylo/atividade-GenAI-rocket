from pydantic_ai.messages import ModelMessage, ModelRequest, UserPromptPart


def is_user_turn(message: ModelMessage) -> bool:
    return isinstance(message, ModelRequest) and any(
        isinstance(part, UserPromptPart) for part in message.parts
    )


def keep_recent_turns(messages: list[ModelMessage], max_turns: int) -> list[ModelMessage]:
    starts = [index for index, message in enumerate(messages) if is_user_turn(message)]
    if len(starts) <= max_turns:
        return messages
    return messages[starts[-max_turns] :]
