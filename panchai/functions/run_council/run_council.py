#input_type_name: RunCouncilInput
#output_type_name: RunCouncilOutput
#function_name: run_council

import asyncio
from typing import List, Dict
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class RunCouncilInput(BaseModel):
    agent_ids: List[str]
    prompt: str


class AgentResponse(BaseModel):
    agent_id: str
    response: str
    error: str = None


class RunCouncilOutput(BaseModel):
    responses: List[AgentResponse]


async def run_council(ctx: FunctionContext, data: RunCouncilInput) -> RunCouncilOutput:
    pod = Pod.from_env()

    async def _run_agent(agent_id: str):
        agent_name = agent_id.replace("_", "-")
        last_error = ""
        for attempt in range(3):
            try:
                # 1. Create conversation for this agent
                conv = pod.conversations.create_for_agent(agent_name, title=f"Council task for {agent_id} (Attempt {attempt+1})")
                conv_id = conv.to_dict()["id"]
                
                # 2. Send the message and collect the response
                full_response = ""
                async for event in pod.conversations.stream(str(conv_id), data.prompt):
                    if event.get("type") == "text":
                        full_response += event.get("content", "")
                        
                if full_response.strip():
                    return AgentResponse(agent_id=agent_id, response=full_response)
                else:
                    raise ValueError("Empty response received from agent conversation stream")
            except Exception as e:
                last_error = str(e)
                # Exponential backoff delay
                await asyncio.sleep(1.0 * (attempt + 1))
                
        return AgentResponse(agent_id=agent_id, response="", error=f"Failed after 3 attempts. Last error: {last_error}")

    # Run all agents in parallel
    tasks = [_run_agent(aid) for aid in data.agent_ids]
    results = await asyncio.gather(*tasks)

    return RunCouncilOutput(responses=list(results))
