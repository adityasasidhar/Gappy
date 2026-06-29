#input_type_name: WriteInput
#output_type_name: WriteOutput
#function_name: write_db_record

import json
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class WriteInput(BaseModel):
    table_name: str
    data_json: str


class WriteOutput(BaseModel):
    record_id: str
    success: bool


async def write_db_record(ctx: FunctionContext, data: WriteInput) -> WriteOutput:
    pod = Pod.from_env()
    payload = json.loads(data.data_json)
    record = pod.records.create(data.table_name, payload)
    rid_obj = getattr(record, "id", record)
    if isinstance(rid_obj, dict):
        rid = rid_obj.get("id", "")
    elif hasattr(rid_obj, "id"):
        rid = rid_obj.id
    else:
        rid = str(rid_obj)
    return WriteOutput(record_id=str(rid), success=True)
