"""A2A protocol helper functions."""

import httpx
import asyncio
import uuid

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    Part,
    TextPart,
    MessageSendParams,
    Message,
    Role,
    SendMessageRequest,
    SendMessageResponse,
)


async def get_agent_card(url: str) -> AgentCard | None:
    """Retrieve an agent's card from its URL.

    Args:
        url: Base URL of the agent

    Returns:
        AgentCard if available, None otherwise
    """
    httpx_client = httpx.AsyncClient()
    resolver = A2ACardResolver(httpx_client=httpx_client, base_url=url)
    card: AgentCard | None = await resolver.get_agent_card()
    return card


async def wait_agent_ready(url: str, timeout: int = 10) -> bool:
    """Wait for an agent to become ready by polling its card.

    Args:
        url: Base URL of the agent
        timeout: Maximum seconds to wait

    Returns:
        True if agent became ready, False if timeout
    """
    retry_cnt = 0
    while retry_cnt < timeout:
        retry_cnt += 1
        try:
            card = await get_agent_card(url)
            if card is not None:
                return True
            else:
                print(f"Agent card not available yet, retrying {retry_cnt}/{timeout}")
        except Exception:
            pass
        await asyncio.sleep(1)
    return False


async def send_message(
    url: str, message: str, task_id: str | None = None, context_id: str | None = None
) -> SendMessageResponse:
    """Send a message to an agent via A2A protocol.

    Args:
        url: Base URL of the agent
        message: Text message to send
        task_id: Optional task ID for task tracking
        context_id: Optional context ID for conversation continuity

    Returns:
        Agent's response
    """
    card = await get_agent_card(url)
    httpx_client = httpx.AsyncClient(timeout=120.0)
    client = A2AClient(httpx_client=httpx_client, agent_card=card)

    message_id = uuid.uuid4().hex
    params = MessageSendParams(
        message=Message(
            role=Role.user,
            parts=[Part(TextPart(text=message))],
            message_id=message_id,
            task_id=task_id,
            context_id=context_id,
        )
    )
    request_id = uuid.uuid4().hex
    req = SendMessageRequest(id=request_id, params=params)
    response = await client.send_message(request=req)
    return response
