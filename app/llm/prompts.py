# app/llm/prompts.py
"""
Prompt templates for AI reasoning.
Centralized prompt management for consistency and testability.
"""

from typing import Dict, Any


class PIAgentPrompts:
    """
    Prompts for the Planning & Intake Agent.
    
    Why centralized: Makes it easy to A/B test prompts, version them,
    and keep agent logic separate from prompt engineering.
    """
    
    @staticmethod
    def build_goal_refinement_prompt(
        original_goal: str,
        user_profession: str,
        user_institution: str,
        num_files: int
    ) -> Dict[str, str]:
        """
        Builds the system and user prompts for goal refinement.
        
        Returns:
            Dict with 'system' and 'user' keys containing the prompts
        """
        system_prompt = f"""You are a Planning & Intake Agent for BridgeScienceAI, helping researchers refine vague research goals into specific, actionable questions.

Your role:
- Analyze the user's research goal and refine it into a clear, specific question
- Consider the user's domain expertise ({user_profession})
- Identify key scientific domains involved
- Recommend 2-4 initial research tasks
- Assess project complexity (Low, Medium, High)

Output requirements:
- Be specific and concrete (avoid vague statements)
- Use scientific terminology appropriate for the domain
- Tasks should be actionable and ordered logically
- Explain your reasoning clearly

The user is a {user_profession} from {user_institution}."""

        user_prompt = f"""Research Goal:
{original_goal}

Context: The user has provided {num_files} supporting document(s).

Please analyze this goal and provide:
1. A refined, specific research question
2. Your reasoning for how/why you refined it
3. 2-4 recommended initial tasks
4. Complexity assessment (Low/Medium/High)
5. Key scientific domains involved

Respond in valid JSON format matching this structure:
{{
  "refined_goal": "Specific research question here",
  "reasoning": "Explanation of refinement",
  "recommended_tasks": [
    {{"description": "Task 1", "rationale": "Why this matters"}},
    {{"description": "Task 2", "rationale": "Why this matters"}}
  ],
  "estimated_complexity": "Medium",
  "key_domains": ["Domain 1", "Domain 2"]
}}"""

        return {
            "system": system_prompt,
            "user": user_prompt
        }