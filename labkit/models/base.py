"""
Base models and validators for Labbook specification
"""

import re
from typing import Union, List, Dict, Any, Optional
from pydantic import BaseModel, Field, constr

# 统一的时间表达式正则，支持 1h2m3s4ms
TIME_EXPR_REGEX = r'^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?(?:(\d+)ms)?$'
TimeExpression = constr(pattern=TIME_EXPR_REGEX)

class BaseLabbookModel(BaseModel):
    """Base model for all Labbook components"""
    class Config:
        validate_assignment = True
        extra = "forbid"
        use_enum_values = True

class ValidationError(Exception):
    """Custom validation error for Labbook models"""
    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)
    def __str__(self):
        if self.errors:
            error_details = "\n".join([f"- {e}" for e in self.errors])
            return f"{self.message}\n{error_details}"
        return self.message 