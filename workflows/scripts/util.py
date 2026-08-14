from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
type JsonDict = dict[str, JsonValue]

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class AllowExtraPydanticModel(BaseModel):
    model_config = ConfigDict(extra="allow")