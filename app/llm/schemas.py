# app/llm/schemas.py
"""
Pydantic schemas for structured LLM outputs.

Why: These define the CONTRACT for what the AI should return.
If the AI returns malformed data, Pydantic validation catches it.
"""

from pydantic import BaseModel, Field
from typing import List


class TaskRecommendation(BaseModel):
    """
    A single task in the initial research plan.
    """
    description: str = Field(
        ...,
        description="What needs to be done (action-oriented)",
        min_length=10,
        max_length=500
    )
    rationale: str = Field(
        ...,
        description="Why this task is important for the research goal",
        min_length=10,
        max_length=500
    )


class PIAgentOutput(BaseModel):
    """
    Structured output from the PI Agent's LLM reasoning.

    Why: This enforces what the AI must provide. If the LLM hallucinates
    or returns garbage, Pydantic validation fails and we catch it BEFORE
    it reaches the user.

    This is the contract between the LLM and our system.
    """
    refined_goal: str = Field(
        ...,
        description="The clarified, specific research question",
        min_length=20,
        max_length=1000
    )

    reasoning: str = Field(
        ...,
        description="Explanation of how/why the goal was refined",
        min_length=20,
        max_length=2000
    )

    recommended_tasks: List[TaskRecommendation] = Field(
        ...,
        description="Initial breakdown of tasks (2-5 tasks)",
        min_length=2,
        max_length=5
    )

    estimated_complexity: str = Field(
        ...,
        description="Complexity assessment: Low, Medium, or High",
        pattern="^(Low|Medium|High)$"  # Regex validation for exact values
    )

    key_domains: List[str] = Field(
        ...,
        description="Scientific domains involved (e.g., 'Immunology', 'Machine Learning')",
        min_length=1,
        max_length=5
    )
