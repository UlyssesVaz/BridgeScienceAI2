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

    @staticmethod
    def build_post_analysis_prompt(
        original_goal: str,
        user_profession: str,
        user_institution: str,
        document_findings: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Builds prompts for Run 3 (post-analysis) when document analysis is complete.

        This version includes the actual document content that was analyzed.

        Args:
            original_goal: User's original research goal
            user_profession: User's profession
            user_institution: User's institution
            document_findings: Dictionary with 'full_text', 'summary', 'key_points'

        Returns:
            Dict with 'system' and 'user' keys containing the prompts
        """
        system_prompt = f"""You are a Planning & Intake Agent for BridgeScienceAI, helping researchers design experiments based on analyzed documents.

Your role:
- Review the document analysis that was completed
- Refine the user's research goal based on the document content
- Design 2-4 concrete experiment/research tasks based on the findings
- Assess project complexity (Low, Medium, High)
- Identify key scientific domains involved

Output requirements:
- Tasks should be EXPERIMENT DESIGN tasks, not document reading tasks
- Be specific and actionable
- Reference findings from the documents
- Use scientific terminology appropriate for the domain

The user is a {user_profession} from {user_institution}."""

        # Extract document summary (limit to avoid token bloat)
        doc_summary = document_findings.get('summary', 'No summary available')[:1000]
        doc_preview = document_findings.get('full_text', '')[:2000]  # First 2000 chars

        user_prompt = f"""Original Research Goal:
{original_goal}

Document Analysis Complete:
{doc_summary}

Document Content Preview:
{doc_preview}

Based on this analysis, please:
1. Refine the research goal to be specific and actionable
2. Design 2-4 experiment/research tasks that BUILD ON the document findings
3. Assess complexity and identify domains

Respond in valid JSON format matching this structure:
{{
  "refined_goal": "Specific research question based on the documents",
  "reasoning": "How the documents inform this goal",
  "recommended_tasks": [
    {{"description": "Design experiment for X", "rationale": "Why this matters based on findings"}},
    {{"description": "Analyze Y using Z method", "rationale": "Why this matters based on findings"}}
  ],
  "estimated_complexity": "Medium",
  "key_domains": ["Domain 1", "Domain 2"]
}}"""

        return {
            "system": system_prompt,
            "user": user_prompt
        }