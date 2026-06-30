#input_type_name: BatchWriteInput
#output_type_name: BatchWriteOutput
#function_name: batch_write

import json
import re
from typing import List, Optional
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class WriteItem(BaseModel):
    table_name: str
    data_json: str


class BatchWriteInput(BaseModel):
    writes: List[WriteItem]


class RecordResult(BaseModel):
    index: int
    record_id: str
    success: bool
    error: Optional[str] = None


class BatchWriteOutput(BaseModel):
    results: List[RecordResult]


async def batch_write(ctx: FunctionContext, data: BatchWriteInput) -> BatchWriteOutput:
    pod = Pod.from_env()
    id_map: dict[int, str] = {}
    results = []

    for idx, item in enumerate(data.writes):
        try:
            payload_str = item.data_json
            # Replace $ref:N with the record_id of index N (N must be <= idx)
            def _replace_ref(m: re.Match) -> str:
                ref_idx = int(m.group(1))
                if ref_idx in id_map:
                    return id_map[ref_idx]
                return m.group(0)

            payload_str = re.sub(r'\$ref:(\d+)', _replace_ref, payload_str)
            payload = json.loads(payload_str)
            record = pod.records.create(item.table_name, payload)
            rid_obj = getattr(record, "id", record)
            if isinstance(rid_obj, dict):
                rid = rid_obj.get("id", "")
            elif hasattr(rid_obj, "id"):
                rid = rid_obj.id
            else:
                rid = str(rid_obj)
            rid_str = str(rid)
            id_map[idx] = rid_str
            results.append(RecordResult(index=idx, record_id=rid_str, success=True))
        except Exception as e:
            results.append(RecordResult(index=idx, record_id="", success=False, error=str(e)))
    return BatchWriteOutput(results=results)
