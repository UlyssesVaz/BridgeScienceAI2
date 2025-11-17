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

    MULTI-RUN ARCHITECTURE:
    - Run 1 (Initial): Creates execution task, hands to analyst_agent
    - Run 3 (Post-Analysis): Generates experiment tasks, sets user_approval checkpoint

    Detection logic: Checks for scratchpad['findings'] to determine which run.
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
        
        # DETECT: Is this Run 1 (initial) or Run 3 (post-analysis)?
        analysis_complete = state.scratchpad.get('findings') is not None

        # Log initial action (lightweight provenance only)
        state.add_audit_entry(
            agent="pi_agent",
            action="planning_initiated",
            details={
                "num_context_files": num_files,
                "run_type": "post_analysis" if analysis_complete else "initial"
            }
        )

        try:
            # BRANCH: Run 1 (Initial) - Files need analysis
            if not analysis_complete and num_files > 0:
                return await self._execute_run1_initial(
                    state, original_research_goal, user_metadata, num_files
                )

            # BRANCH: Run 3 (Post-Analysis) - Generate experiment tasks
            # This includes the case where analysis is complete OR no files were provided

            # 1. Build the prompt (different prompt if we have document findings)
            if analysis_complete:
                # Use post-analysis prompt with document findings
                document_findings = state.scratchpad.get('findings', {})
                prompts = PIAgentPrompts.build_post_analysis_prompt(
                    original_goal=original_research_goal,
                    user_profession=user_profession,
                    user_institution=user_institution,
                    document_findings=document_findings
                )
                logger.info("Using post-analysis prompt with document findings")
            else:
                # No files provided, use standard refinement prompt
                prompts = PIAgentPrompts.build_goal_refinement_prompt(
                    original_goal=original_research_goal,
                    user_profession=user_profession,
                    user_institution=user_institution,
                    num_files=num_files
                )
                logger.info("Using standard refinement prompt (no files)")
            
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
            
            # 4. Store structured data in scratchpad (machine-readable only)
            state.scratchpad['refined_research_goal'] = validated_output.refined_goal
            state.scratchpad['complexity'] = validated_output.estimated_complexity
            state.scratchpad['domains'] = validated_output.key_domains
            # Note: reasoning is discarded - not needed after initial refinement

            # 5. Add concise checkpoint message (UI-ready format)
            # Format matches the checkpoint wireframe pattern
            domains_display = ', '.join(validated_output.key_domains[:3])  # Limit to 3 for brevity
            if len(validated_output.key_domains) > 3:
                domains_display += f" +{len(validated_output.key_domains) - 3} more"

            state.messages.append(
                ConversationMessage(
                    role="assistant",
                    content=(
                        f"✓ I've analyzed your research goal.\n\n"
                        f"Let me confirm my understanding:\n"
                        f"• **Goal:** {validated_output.refined_goal}\n"
                        f"• **Complexity:** {validated_output.estimated_complexity}\n"
                        f"• **Domains:** {domains_display}\n"
                        f"• **Next Steps:** {len(validated_output.recommended_tasks)} tasks identified\n\n"
                        f"Is this correct?"
                    )
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
            
            # 8. Lightweight audit entry (provenance only, no verbose details)
            state.add_audit_entry(
                agent="pi_agent",
                action="goal_refined",
                details={
                    "complexity": validated_output.estimated_complexity,
                    "num_tasks": len(state.task_list)
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

    async def _execute_run1_initial(
        self,
        state: VirtualLabState,
        original_research_goal: str,
        user_metadata: Dict[str, Any],
        num_files: int
    ) -> VirtualLabState:
        """
        Run 1 (Initial): Create execution task and hand to analyst_agent.

        This is the first pass when context files are provided.
        We create a single task for the analyst_agent to analyze the files,
        then hand control to it.

        Args:
            state: Current VirtualLabState
            original_research_goal: User's research goal
            user_metadata: User context
            num_files: Number of context files

        Returns:
            Updated VirtualLabState with execution task
        """
        logger.info("PI Agent Run 1: Creating execution task for analyst_agent")

        # Create a single execution task
        execution_task = TaskItem(
            id="t1",
            description=f"Analyze {num_files} context document(s) and extract key findings",
            status="pending",
            result=None
        )

        state.task_list = [execution_task]

        # Add concise message
        state.messages.append(
            ConversationMessage(
                role="assistant",
                content=f"I've received your research goal and {num_files} document(s). Analyzing now..."
            )
        )

        # Hand control to analyst_agent
        state.current_phase = "analysis_pending"
        state.next_agent = "analyst_agent"

        # Audit log
        state.add_audit_entry(
            agent="pi_agent",
            action="execution_task_created",
            details={
                "next_agent": "analyst_agent",
                "num_files": num_files
            }
        )

        logger.info(
            "PI Agent Run 1 complete: Handing to analyst_agent",
            extra={"next_agent": state.next_agent}
        )

        return state