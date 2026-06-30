#input_type_name: SpeedInput
#output_type_name: SpeedOutput
#function_name: test_speed

import json
import time
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class SpeedInput(BaseModel):
    agent: str = "tiny-council"
    prompt: str = "Say OK"


class SpeedOutput(BaseModel):
    elapsed: float = 0
    response: str = ""
    error: str = ""


async def test_speed(ctx: FunctionContext, data: SpeedInput) -> SpeedOutput:
    pod = Pod.from_env()
    t0 = time.time()
    try:
        conv = pod.conversations.create_for_agent(data.agent, title="speed test")
        conv_id = str(conv.to_dict()["id"])
        full = ""
        async for event in pod.conversations.stream(conv_id, data.prompt):
            if event.get("type") == "text":
                full += event.get("content", "")
        elapsed = time.time() - t0
        return SpeedOutput(elapsed=elapsed, response=full[:500])
    except Exception as e:
        elapsed = time.time() - t0
        return SpeedOutput(elapsed=elapsed, error=str(e))
