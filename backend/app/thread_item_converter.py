"""Helpers that convert ChatKit thread items into model-friendly inputs."""

from __future__ import annotations

from chatkit.agents import ThreadItemConverter
from chatkit.types import HiddenContextItem, WidgetItem
from openai.types.responses import ResponseInputTextParam
from openai.types.responses.response_input_item_param import Message


class SeaPayThreadItemConverter(ThreadItemConverter):
    """Adds support for hidden context and prevents widgets from being added to chat history."""

    async def hidden_context_to_input(self, item: HiddenContextItem):
        return Message(
            type="message",
            content=[
                ResponseInputTextParam(
                    type="input_text",
                    text=item.content,
                )
            ],
            role="user",
        )

    async def widget_to_input(self, item: WidgetItem):
        """
        Override to prevent widgets from being converted to user messages in chat history.
        Returns None so widgets are excluded from the conversation context sent to the model.
        """
        return None
