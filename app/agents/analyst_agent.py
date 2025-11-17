# app/agents/analyst_agent.py

from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import PyPDF2

from .base import BaseAgent, VirtualLabState
from app.schemas.project import ConversationMessage, TaskItem

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """
    Analyst Agent - Reads and analyzes context documents.

    CURRENT STATE: Skeletal implementation with placeholder logic
    - Simple text extraction from files
    - Populates scratchpad with structured findings
    - No LLM analysis yet
    - No external tool calls yet

    FUTURE ENHANCEMENTS:
    - Full PDF parsing with PyPDF2/pdfplumber
    - LLM-based extraction of key findings
    - Integration with SearchAgent for web research
    - Multi-document synthesis

    Responsibilities:
    - Read context files provided by user
    - Extract text content (placeholder: first 1000 chars)
    - Populate scratchpad with structured data
    - Hand control back to PI Agent for final planning
    """

    def __init__(self):
        """Initialize Analyst Agent."""
        pass

    async def execute(
        self,
        state: VirtualLabState,
        original_research_goal: str,
        user_metadata: Dict[str, Any],
        context_files: Optional[List[str]] = None,
        **kwargs
    ) -> VirtualLabState:
        """
        Analyze context documents and populate scratchpad.

        Args:
            state: Current VirtualLabState
            original_research_goal: User's research goal
            user_metadata: User context (profession, etc.)
            context_files: List of file paths to analyze

        Returns:
            Updated VirtualLabState with findings in scratchpad
        """
        logger.info(
            "Analyst Agent execution started",
            extra={
                "user_id": user_metadata.get('user_id'),
                "num_files": len(context_files) if context_files else 0
            }
        )

        # Audit log entry
        state.add_audit_entry(
            agent="analyst_agent",
            action="analysis_initiated",
            details={
                "num_context_files": len(context_files) if context_files else 0
            }
        )

        try:
            # PLACEHOLDER LOGIC: Simple text extraction
            findings = await self._analyze_files_placeholder(context_files)

            # Populate scratchpad with structured data
            # Using the exact structure you specified
            state.scratchpad['findings'] = findings
            state.scratchpad['primary_domains'] = self._extract_domains_placeholder(findings)
            state.scratchpad['ai_execution_time_hr'] = 0.5  # Placeholder estimate
            state.scratchpad['target_methodology'] = 'Experimental Design'
            state.scratchpad['required_tools'] = ['LLM', 'DocumentAnalysis']
            state.scratchpad['required_external_data'] = 'None'
            state.scratchpad['task_rationale_summary'] = (
                f"Analysis of {len(context_files) if context_files else 0} document(s) complete. "
                "Ready to generate experiment design tasks."
            )

            # Add message to conversation history
            state.messages.append(
                ConversationMessage(
                    role="assistant",
                    content=f"✓ Document analysis complete. Analyzed {len(context_files) if context_files else 0} file(s)."
                )
            )

            # Update state - hand control back to PI Agent
            state.current_phase = "analysis_complete"
            state.next_agent = "pi_agent"

            # Audit log
            state.add_audit_entry(
                agent="analyst_agent",
                action="analysis_complete",
                details={
                    "findings_length": len(findings.get('summary', '')),
                    "domains_identified": len(state.scratchpad.get('primary_domains', []))
                }
            )

            logger.info(
                "Analyst Agent execution completed",
                extra={
                    "findings_length": len(findings.get('summary', '')),
                    "next_agent": state.next_agent
                }
            )

            return state

        except Exception as e:
            logger.error(
                "Analyst Agent execution failed",
                extra={"error": str(e)},
                exc_info=True
            )

            state.add_audit_entry(
                agent="analyst_agent",
                action="analysis_failed",
                details={"error": str(e)}
            )

            raise

    async def _analyze_files_placeholder(self, file_paths: Optional[List[str]]) -> Dict[str, Any]:
        """
        Extracts text content from files (PDF and text).

        CURRENT: Proper PDF text extraction with PyPDF2
        FUTURE: Add LLM-based analysis of extracted content

        Args:
            file_paths: List of file paths to analyze

        Returns:
            Dictionary with extracted findings
        """
        if not file_paths:
            return {
                'summary': 'No context files provided.',
                'key_points': [],
                'file_count': 0,
                'full_text': ''
            }

        findings = {
            'summary': '',
            'key_points': [],
            'file_count': len(file_paths),
            'full_text': ''
        }

        for file_path in file_paths:
            try:
                path = Path(file_path)

                if not path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue

                # Extract text based on file type
                extracted_text = ''

                if path.suffix.lower() == '.pdf':
                    # PDF extraction
                    extracted_text = self._extract_text_from_pdf(path)
                    logger.info(f"Extracted {len(extracted_text)} chars from PDF: {path.name}")
                else:
                    # Plain text file
                    with open(path, 'r', errors='ignore') as f:
                        extracted_text = f.read()
                    logger.info(f"Read {len(extracted_text)} chars from text file: {path.name}")

                # Store findings
                findings['full_text'] += f"\n\n=== {path.name} ===\n{extracted_text}"
                findings['summary'] += f"\n[{path.name}]: {len(extracted_text)} characters extracted"
                findings['key_points'].append(f"Analyzed {path.name}: {len(extracted_text)} chars")

            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}", exc_info=True)
                findings['key_points'].append(f"Error reading {path.name}: {str(e)}")

        # Create a summary snippet (first 500 chars of full text)
        if findings['full_text']:
            snippet = findings['full_text'][:500]
            findings['summary'] += f"\n\nContent preview:\n{snippet}..."

        return findings

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file using PyPDF2.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        try:
            text_content = []

            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)

                logger.info(f"Reading PDF: {pdf_path.name} ({num_pages} pages)")

                # Extract text from all pages
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text_content.append(page_text)

                full_text = '\n\n'.join(text_content)
                logger.info(f"Extracted {len(full_text)} characters from {num_pages} pages")

                return full_text

        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}", exc_info=True)
            return f"[Error extracting PDF: {str(e)}]"

    def _extract_domains_placeholder(self, findings: Dict[str, Any]) -> List[str]:
        """
        PLACEHOLDER: Simple domain extraction.

        FUTURE: Use LLM to identify scientific domains from findings.

        Args:
            findings: Extracted findings dictionary

        Returns:
            List of identified domains
        """
        # PLACEHOLDER: Return generic domains
        # FUTURE: LLM-based domain classification
        return ['Computational Biology', 'Data Analysis']
