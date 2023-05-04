from langchain.output_parsers import OutputFixingParser, PydanticOutputParser

from src.tools.context import ToolContext
from src.utils.prompt import Prompter, PromptString
from ..utils.database.database import supabase 
from ..utils.models import ChatModel
from ..utils.parameters import DEFAULT_FAST_MODEL, DEFAULT_SMART_MODEL


from pydantic import BaseModel, Field, validator


class HasHappenedLLMResponse(BaseModel):
    has_happened: bool = Field(description="Whether the event has happened or not")
    date_occured: str = Field(description="The date and time the event occured, in this format: %Y-%m-%d %H:%M:%S")


async def wait_async(agent_input: str, tool_context: ToolContext) -> str:
    """Wait for a specified event to occur."""

    # Recent memories
    (_, memories), count = (
        supabase.table("Memories").select("*").eq("agent_id", str(tool_context.agent_id)).limit(5).execute()
    )
    memories = [f"{m['description']} @ {m['created_at']}" for m in memories]

    # Set up the LLM, Parser, and Prompter
    llm = ChatModel(temperature=0)
    parser = OutputFixingParser.from_llm(
        parser=PydanticOutputParser(pydantic_object=HasHappenedLLMResponse),
        llm=llm.defaultModel,
    )
    prompter = Prompter(
        PromptString.HAS_HAPPENED, 
        {
            "memory_descriptions": "-" + "\n-".join(memories), 
            "event_description": agent_input,
            "format_instructions": parser.get_format_instructions()
        }
    )

    # Get the response
    response = await quick_llm.get_chat_completion(
        prompter.prompt,
        loading_text="Checking if event has happened...",
    )

    # Parse the response
    parsed_response: HasHappenedLLMResponse = parser.parse(response)

    if parsed_response.has_happened:
        return f"The event I was waiting for occured at {parsed_response.date_occured}. No need to wait anymore."
    else:
        return "The event I was waiting for has not happened yet. Waiting..."


def wait_sync(agent_input: str, tool_context: ToolContext) -> str:
    """Wait for a specified event to occur."""

    raise NotImplementedError("This tool is not implemented in sync mode")