# app/agents/pi_agent.py

from typing import Dict, List, Any, Optional
import json
import logging

from .base import BaseAgent, VirtualLabState
from app.schemas.project import ConversationMessage, TaskItem
from app.llm.openai_provider import OpenAIProvider
from app.llm.prompts import PIAgentPrompts
from app.llm.schemas import PIAgentOutput

logger = logging.getLogger(__name__)


class PIAgent(BaseAgent):
    """
    Planning & Intake Agent
    Responsible for refining research goals and creating initial task plans.
    """
    
    def __init__(self, llm_provider: Optional[OpenAIProvider] = None):
        """
        Initialize PI Agent with LLM provider.
        
        Args:
            llm_provider: LLM provider to use (defaults to OpenAI GPT-4)
        """
        self.llm = llm_provider or OpenAIProvider(model="gpt-4")
    
    async def execute(
        self,
        state: VirtualLabState,
        original_research_goal: str,
        user_metadata: Dict[str, Any],
        context_files: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> VirtualLabState:
        """
        Analyzes research goal using LLM and creates refined plan.
        
        Args:
            state: The initial state workbench
            original_research_goal: The user's goal
            user_metadata: User context (profession, institution)
            context_files: List of file metadata
        """
        user_profession = user_metadata.get('profession', 'Scientist')
        user_institution = user_metadata.get('institution', 'Research Institution')
        num_files = len(context_files) if context_files else 0
        
        logger.info(
            "PI Agent execution started",
            extra={
                "user_id": user_metadata.get('user_id'),
                "profession": user_profession,
                "num_files": num_files
            }
        )
        
        # Log initial action
        state.add_audit_entry(
            agent="pi_agent",
            action="planning_initiated",
            details={
                "user_profession": user_profession,
                "original_research_goal": original_research_goal,
                "num_context_files": num_files
            }
        )
        
        try:
            # 1. Build the prompt
            prompts = PIAgentPrompts.build_goal_refinement_prompt(
                original_goal=original_research_goal,
                user_profession=user_profession,
                user_institution=user_institution,
                num_files=num_files
            )
            
            # 2. Call LLM
            logger.debug("Calling LLM for goal refinement")
            llm_response = await self.llm.generate(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                max_tokens=2000,
                temperature=0.7
            )
            
            logger.info(
                "LLM response received",
                extra={
                    "tokens_used": llm_response.metadata.get("usage", {}).get("total_tokens", 0)
                }
            )
            
            # 3. Parse and validate LLM output
            try:
                parsed_json = json.loads(llm_response.content)
                validated_output = PIAgentOutput(**parsed_json)
            except json.JSONDecodeError as e:
                logger.error(f"LLM returned invalid JSON: {e}", exc_info=True)
                raise ValueError(f"LLM response was not valid JSON: {e}")
            except Exception as e:
                logger.error(f"LLM output failed validation: {e}", exc_info=True)
                raise ValueError(f"LLM output validation failed: {e}")
            
            # 4. Store refined goal in scratchpad
            state.scratchpad['refined_research_goal'] = validated_output.refined_goal
            state.scratchpad['reasoning'] = validated_output.reasoning
            state.scratchpad['complexity'] = validated_output.estimated_complexity
            state.scratchpad['domains'] = validated_output.key_domains
            
            # 5. Add assistant message
            state.messages.append(
                ConversationMessage(
                    role="assistant",
                    content=f"I've analyzed your research goal as a {user_profession}.\n\n"
                           f"**Refined Goal:** {validated_output.refined_goal}\n\n"
                           f"**Reasoning:** {validated_output.reasoning}\n\n"
                           f"**Complexity:** {validated_output.estimated_complexity}\n"
                           f"**Domains:** {', '.join(validated_output.key_domains)}"
                )
            )
            
            # 6. Convert LLM tasks to TaskItems
            state.task_list = [
                TaskItem(
                    id=f"t{idx+1}",
                    description=task.description,
                    status="pending",
                    result=task.rationale  # Store rationale in result field for now
                )
                for idx, task in enumerate(validated_output.recommended_tasks)
            ]
            
            # 7. Update state
            state.current_phase = "planning_complete"
            state.next_agent = "user_approval"
            
            # 8. Final audit entry
            state.add_audit_entry(
                agent="pi_agent",
                action="planning_complete",
                details={
                    "refined_research_goal": validated_output.refined_goal,
                    "tasks_created": len(state.task_list),
                    "complexity": validated_output.estimated_complexity,
                    "domains": validated_output.key_domains,
                    "next_agent": state.next_agent
                }
            )
            
            logger.info(
                "PI Agent execution completed successfully",
                extra={
                    "refined_goal_length": len(validated_output.refined_goal),
                    "num_tasks": len(state.task_list),
                    "complexity": validated_output.estimated_complexity
                }
            )
            
            return state
            
        except Exception as e:
            # Log error and add to audit trail
            logger.error(
                "PI Agent execution failed",
                extra={"error": str(e)},
                exc_info=True
            )
            
            state.add_audit_entry(
                agent="pi_agent",
                action="planning_failed",
                details={"error": str(e)}
            )
            
            raise