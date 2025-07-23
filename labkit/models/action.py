from pydantic import Field
from enum import Enum
from typing import Any, Dict, Optional
from labkit.models.base import BaseLabbookModel

class ActionType(str, Enum):
    NETWORK_EVENTS = "network-events"
    NETFUNC_EVENTS = "netfunc-events"
    NETFUNC_EXEC_OUTPUT = "netfunc-exec-output"

class Action(BaseLabbookModel):
    """
    experiment: 实验设计, 流程, 步骤, 执行动作
    """
    type: ActionType = Field(..., alias="type")
    source: str = Field(..., alias="source")
    with_: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="with")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "type": "network-events",
                "source": "actions/example.yaml",
                "with": {}
            }
        }

    @classmethod
    def template(cls, type_: ActionType, source: str, with_: Optional[Dict[str, Any]] = None) -> "Action":
        return cls(type=type_, source=source, with_=with_)