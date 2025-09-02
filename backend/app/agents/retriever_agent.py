"""
backend/app/agents/retriever_agent.py
"""

from typing import Dict, Any, List, Optional
import logging

# Local application imports
from backend.app.services.document_service import DocumentService
from .state import AgentState, WorkflowStep

logger = logging.getLogger(__name__)


class RetrieverAgent:
    """
    An agent responsible for retrieving relevant context from the knowledge base
    by leveraging the multi-index capabilities of the DocumentService.
    """
    def __init__(self):
        # The agent now uses the DocumentService as its single point of contact
        # for all data retrieval, abstracting away direct database connections.
        try:
            self.document_service = DocumentService()
            print("RetrieverAgent initialized successfully")
        except Exception as e:
            print(f"Failed to initialize DocumentService: {e}")
            self.document_service = None

                # FIX: Define confidence thresholds as instance attributes for robustness.
        self.HIGH_CONFIDENCE_THRESHOLD = 0.70
        self.MEDIUM_CONFIDENCE_THRESHOLD = 0.50
        self.MIN_HIGH_CONFIDENCE_DOCS = 5 # Minimum docs to accept the high-confidence tier

    async def process(self, state: AgentState) -> AgentState:
        """
        Processes the user query to retrieve relevant context using a tiered
        confidence approach.
        """
        ticket_id = state.get("ticket_id", "unknown")
        category = state.get("category", "N/A")
        query = state.get("rewritten_query", state["original_query"])
        user_course_category = state.get("user_course_category")
        user_course_name = state.get("user_course_name")
        
        print(f"RETRIEVER AGENT: Processing ticket '{ticket_id}' with query '{query}'")
        print(f"Original Category: '{category}'")
        print(f"User Course: {user_course_category} - {user_course_name}")

        try:
            if not self.document_service:
                raise Exception("DocumentService not initialized")
            
            # 1. Map the incoming ticket category...
            kb_category = self._get_kb_category(category)
            
            if not kb_category:
                print(f"No knowledge base mapping for category: {category}. Skipping retrieval.")
                state["retrieved_context"] = []
                state["current_step"] = WorkflowStep.RESPONSE_GENERATION.value
                return state

            # 1. Map category and define search scope
            search_categories = [kb_category]
            # if kb_category != 'qa_documents':
            #     search_categories.append('qa_documents')
            
            print(f"Searching in categories: {search_categories}")

            # 2. Perform a single, consolidated search to get a candidate pool
            search_results = await self.document_service.search_documents(
                query=query,
                categories=search_categories,
                top_k=15, # Fetch a larger pool for better filtering
                course_category=user_course_category,
                course_name=user_course_name
            )
            print(f"Retrieved {len(search_results)} total candidate documents.")
            
            if len(search_results) == 0 and kb_category != 'qa_documents':
                search_results = await self.document_service.search_documents(
                    query=query,
                    categories=search_categories,
                    top_k=15, # Fetch a larger pool for better filtering
                    course_category=user_course_category,
                    course_name=user_course_name
                )
                print(f"Retrieved from backup qa_documents {len(search_results)} total candidate documents.")
                

            # 3. Apply the tiered confidence filtering logic
            selected_chunks = []
            
            # Sort results once by score (highest first)
            sorted_results = sorted(search_results, key=lambda x: x.get("score", 0.0), reverse=True)

            # Tier 1: High-Confidence
            high_confidence_results = [
                r for r in sorted_results if r.get("score", 0) >= self.HIGH_CONFIDENCE_THRESHOLD
            ]
            if len(high_confidence_results) >= self.MIN_HIGH_CONFIDENCE_DOCS:
                print(f"SUCCESS: Found {len(high_confidence_results)} documents meeting high-confidence threshold ({self.HIGH_CONFIDENCE_THRESHOLD}).")
                selected_chunks = high_confidence_results

            # Tier 2: Medium-Confidence
            elif not selected_chunks:
                medium_confidence_results = [
                    r for r in sorted_results if r.get("score", 0) >= self.MEDIUM_CONFIDENCE_THRESHOLD
                ]
                if medium_confidence_results:
                    print(f"FALLBACK: Using {len(medium_confidence_results)} documents from medium-confidence threshold ({self.MEDIUM_CONFIDENCE_THRESHOLD}).")
                    selected_chunks = medium_confidence_results

            # Tier 3: Best-Effort Fallback
            if not selected_chunks and sorted_results:
                print("FALLBACK: No documents met thresholds. Using top 5 best-effort results.")
                selected_chunks = sorted_results[:5]
                
            # 4. Re-rank the chunks selected by our tiered logic
            # reranked_chunks = await self._rerank_chunks(selected_chunks, query)

            # 5. Format the final context for the LLM
            final_context = []
            for result in selected_chunks:
                if result.get("potential_response"):
                    result['content'] = (
                        f"A relevant Q&A pair was found in the knowledge base.\n"
                        f"Question: {result.get('text_snippet', '')}\n"
                        f"Answer: {result.get('potential_response')}"
                    )
                else:
                    result['content'] = result.get('text_snippet', '')
                final_context.append(result)

            # 6. Update the state
            state["retrieved_context"] = final_context
            state["current_step"] = WorkflowStep.RESPONSE_GENERATION.value
            
            if not final_context:
                print(f"NO RELEVANT CONTEXT ultimately selected for ticket {ticket_id}.")
            else:
                print(f"SELECTED {len(final_context)} top chunks for context for ticket {ticket_id}.")
                best_chunk = final_context[0]
                print(f"Best chunk details: score={best_chunk.get('score', 0):.3f}, content='{best_chunk.get('content', '')[:100]}...'")

            return state
                
        except Exception as e:
            print(f"RETRIEVER AGENT ERROR for ticket {ticket_id}: {e}")
            state["error_message"] = f"Context retrieval failed: {str(e)}"
            state["requires_escalation"] = True
            state["current_step"] = WorkflowStep.ESCALATION.value
            return state

    def _get_kb_category(self, ticket_category: Optional[str]) -> Optional[str]:
        """
        Maps an incoming ticket category to one of the three main knowledge base categories.
        
        Returns the name of the knowledge base category (e.g., "program_details_documents").
        """
        if not ticket_category:
            print("No category provided, defaulting to qa_documents")
            return "qa_documents"

        # Enhanced mapping with more detailed logging
        category_mapping = {
            # Program and administrative related -> Program Details
            "Course Query": "program_details_documents",
            "Attendance/Counselling Support": "program_details_documents", 
            "Leave": "program_details_documents",
            "Late Evaluation Submission": "program_details_documents",
            "Missed Evaluation Submission": "program_details_documents",
            "Withdrawal": "program_details_documents",
            "Other Course Query": "program_details_documents",
            
            # Technical and curriculum related -> Curriculum Documents
            "Evaluation Score": "curriculum_documents",
            "MAC": "curriculum_documents",
            "Revision": "curriculum_documents",
            
            # General support, FAQs, troubleshooting -> qa_documents
            "Product Support": "qa_documents",
            "NBFC/ISA": "qa_documents",
            "Feedback": "qa_documents",
            "Referral": "qa_documents",
            "Personal Query": "qa_documents",
            "Code Review": "qa_documents",
            "Placement Support - Placements": "qa_documents",
            "Offer Stage- Placements": "qa_documents", 
            "ISA/EMI/NBFC/Glide Related - Placements": "qa_documents",
            "Session Support - Placement": "qa_documents",
            "IA Support": "qa_documents",
        }
        
        mapped_category = category_mapping.get(ticket_category)
        
        if mapped_category:
            print(f"CATEGORY MAPPING: '{ticket_category}' -> '{mapped_category}'")
        else:
            print(f" UNMAPPED CATEGORY: '{ticket_category}', defaulting to 'qa_documents'")
            mapped_category = "qa_documents"
        
        return mapped_category

    async def _rerank_chunks(self, chunks: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Re-ranks retrieved chunks based on relevance score.
        """
        if not chunks:
            print("No chunks to rerank")
            return []
        
        print(f"RERANKING {len(chunks)} chunks based on score.")
        
        # Sort by score (assuming higher scores from Pinecone are better)
        try:
            sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0.0), reverse=True)
            
            if sorted_chunks:
                best_score = sorted_chunks[0].get("score", 0)
                worst_score = sorted_chunks[-1].get("score", 0)
                print(f"Reranked scores range from {best_score:.3f} to {worst_score:.3f}")
            
            return sorted_chunks
            
        except Exception as e:
            print(f"Reranking failed due to an error: {e}, returning original order")
            return chunks