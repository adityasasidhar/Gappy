#input_type_name: UpdateInput
#output_type_name: UpdateOutput
#function_name: update_db_record

import json
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class UpdateInput(BaseModel):
    table_name: str
    record_id: str
    data_json: str


class UpdateOutput(BaseModel):
    success: bool


async def update_db_record(ctx: FunctionContext, data: UpdateInput) -> UpdateOutput:
    pod = Pod.from_env()
    payload = json.loads(data.data_json)
    pod.records.update(data.table_name, data.record_id, payload)
    return UpdateOutput(success=True)
