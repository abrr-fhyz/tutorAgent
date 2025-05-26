from pydantic import BaseModel
from typing import List
import math

class QueryRequest(BaseModel):
    question: str
    mode: str = "off-syllabus"  # "on-syllabus" or "off-syllabus"

class QueryResponse(BaseModel):
    answer: str
    agent_used: str
    tools_used: List[str] = []
    sources: List[str] = []

class Tool:
    """Base class for tools that agents can use"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, *args, **kwargs):
        raise NotImplementedError
    
class CalculatorTool(Tool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Performs basic mathematical calculations"
        )
    
    def execute(self, expression: str) -> float:
        """Safely evaluate mathematical expressions"""
        try:
            expression = expression.replace(" ", "")
            allowed_chars = set("0123456789+-*/().^**")
            if not all(c in allowed_chars for c in expression):
                raise ValueError("Invalid characters in expression")
            
            expression = expression.replace("^", "**")
            
            result = eval(expression, {"__builtins__": {}, "math": math})
            return float(result)
        except Exception as e:
            raise ValueError(f"Calculation error: {str(e)}")