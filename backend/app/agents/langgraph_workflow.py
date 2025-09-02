"""
Enhanced LangGraph Workflow for Intelligent LMS Support System
This module implements a production-ready multi-agent workflow using LangGraph
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
import asyncio
import logging
import json
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate,MessagesPlaceholder
from pydantic import BaseModel, Field
from backend.app.models import ticket_service, conversation_service, user_service, TicketStatus
from backend.app.core.config import settings
from .cache_service import SemanticCacheService
from .retriever_agent import RetrieverAgent
from .escalation_agent import EscalationAgent
import traceback
import re
from typing_extensions import Literal, Annotated
from backend.app.services.analytics_service import analytics_service


logger = logging.getLogger(__name__)

# Enhanced State Definition with LangGraph annotations
class GraphState(TypedDict):
    """State definition for the LangGraph workflow"""
    # Core ticket information
    ticket_id: str
    user_id: str
    original_query: str
    title: str
    category: str
    
    # User course information
    user_course_category: Optional[str]
    user_course_name: Optional[str]

    rewritten_query: Optional[str]

    
    # Workflow tracking
    messages: Annotated[List, add_messages]
    steps_taken: List[str]
    
    # Agent inputs and outputs
    context: str # Unified context from cache or retriever
    agent_decision: Dict[str, Any] # Structured decision from the LLM
    
    # Context and metadata
    conversation_history: List[Dict[str, Any]]
    final_status: Optional[str]
    error_message: Optional[str]

class AgentDecision(BaseModel):
    """Structured output for the agent's decision-making process."""
    decision: Literal['respond', 'request_info', 'escalate'] = Field(description="The final decision. Must be one of: 'respond', 'request_info', 'escalate'.")
    response: Optional[str] = Field(default=None, description="The generated response for the student if the decision is 'respond'.")
    missing_info: Optional[List[str]] = Field(default=None, description="A list of specific information required from the student if the decision is 'request_info'.")
    escalation_reason: Optional[str] = Field(default=None, description="A brief reason for escalation if the decision is 'escalate'.")
    admin_type: Literal['EC', 'IA']  = Field(description="The team responsible for the query. Must be 'EC' or 'IA'.")
    confidence: float = Field(description="Confidence score (0.0 to 1.0) in the decision.")

class RewrittenQuery(BaseModel):
    """Structured output for the query rewriting step."""
    rewritten_query: str = Field(description="A single, optimized search query tailored for a specific knowledge base.")


class EnhancedLangGraphWorkflow:
    """Production-ready LangGraph workflow with a central decision-making agent."""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
            model_kwargs={"response_mime_type": "application/json"}
        )
        self.query_rewriter_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
            model_kwargs={"response_mime_type": "application/json"}
        )
        self.cache_service = SemanticCacheService()
        self.retriever_agent = RetrieverAgent()
        self.escalation_agent = EscalationAgent()
        self.workflow = self._build_workflow()
      
    async def _find_available_admin(self, admin_type: str) -> Dict[str, Any]:
        """
        Finds an available admin.
        In a real system, this would check for load, online status, and specialty.
        For now, it returns the first available admin.
        """
        try:
            # This logic can be expanded to filter by EC/IA roles if they are stored in the user model
            admins = user_service.get_admins(admin_type=admin_type)
            print(f"available admins {admins}.")
            return admins[0] if admins else None
        except Exception as e:
            logger.error(f"Error finding admin: {e}")
            return None
        
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

    def _build_workflow(self) -> StateGraph:
        """Builds the simplified, more powerful LangGraph workflow."""
        print("Building LangGraph workflow...")
        workflow = StateGraph(GraphState)
        
        # Define the nodes
        workflow.add_node("initialize", self.initialize_state)
        workflow.add_node("check_cache", self.check_cache)
        workflow.add_node("retrieve_context", self.retrieve_context)
        workflow.add_node("generate_and_decide", self.generate_and_decide)
        workflow.add_node("finalize_and_act", self.finalize_and_act)
        workflow.add_node("rewrite_query_for_retrieval", self.rewrite_query_for_retrieval) 
        
        # Define the graph structure
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "check_cache")
        
        # --- MODIFIED FOR QUERY REWRITING ---
        workflow.add_conditional_edges(
            "check_cache",
            # On cache miss, go to rewrite. On hit, go to decide.
            lambda state: "rewrite_query_for_retrieval" if state.get("context") is None else "generate_and_decide",
            {
                "rewrite_query_for_retrieval": "rewrite_query_for_retrieval",
                "generate_and_decide": "generate_and_decide"
            }
        )
        workflow.add_edge("rewrite_query_for_retrieval", "retrieve_context")
        
        workflow.add_edge("retrieve_context", "generate_and_decide")
        workflow.add_edge("generate_and_decide", "finalize_and_act")
        workflow.add_edge("finalize_and_act", END)
        
        return workflow.compile()

    async def initialize_state(self, state: GraphState) -> GraphState:
        """Initialize the workflow state with ticket information."""
        print(f"INITIALIZING STATE for ticket {state['ticket_id']}")
        try:
            # Run blocking calls in a separate thread
            ticket = await asyncio.to_thread(
                ticket_service.get_ticket_by_id, state["ticket_id"]
            )
            if not ticket:
                raise ValueError(f"Ticket {state['ticket_id']} not found")

            conversations = await asyncio.to_thread(conversation_service.get_ticket_conversations, state["ticket_id"])
            
            # Fetch user course information
            user = await asyncio.to_thread(user_service.get_user_by_id, ticket["user_id"])
            user_course_category = user.get("course_category") if user else None
            user_course_name = user.get("course_name") if user else None
            
            messages = []
            for conv in conversations:
                message_content = conv["message"] if conv["message"] is not None else "[Message content not available]"
                if conv["sender_role"] == "student":
                    messages.append(HumanMessage(content=message_content))
                else:
                    # Assuming 'agent' or 'support' roles are the AI
                    messages.append(AIMessage(content=message_content))
            print("Updating state category", ticket["category"], ticket['title'])
            print("Original Query: ", conversations[-1]['message'] if conversations and conversations[-1] and 'message' in conversations[-1] else "No original query available")
            print(f"User course info: {user_course_category} - {user_course_name}")
            state.update({
                "user_id": str(ticket["user_id"]),
                "original_query": conversations[-1]['message'] if conversations and conversations[-1] and 'message' in conversations[-1] else "No original query available", # The latest message is the current query
                "title": ticket["title"],
                "category": ticket["category"],
                "user_course_category": user_course_category,
                "user_course_name": user_course_name,
                "messages": messages,
                "steps_taken": ["initialize"]
            })
            print(f"INITIALIZED STATE: category={state['category']}, query='{state['original_query'][:50]}...'")
            return state
        except Exception as e:
            print(f"INITIALIZATION ERROR: {e}")
            state["error_message"] = str(e)
            return state

    async def check_cache(self, state: GraphState) -> GraphState:
        """Check semantic cache for similar resolved queries."""
        print(f"CHECKING CACHE for ticket {state['ticket_id']}")
        cached_result = await self.cache_service.search_similar(
            query=state["original_query"],
            course_category=state.get("user_course_category"),
            course_name=state.get("user_course_name"),
            threshold=0.65
        )
        
        def sanitize_kb_content(content: str) -> str:
                # Remove greetings, closings, personal names, phone numbers
                content = re.sub(r"Dear .*?,", "", content)
                content = re.sub(r"Thanks.*", "", content, flags=re.IGNORECASE | re.DOTALL)
                content = re.sub(r"Thank you *", "", content, flags=re.IGNORECASE | re.DOTALL)
                content = re.sub(r"\+?\d[\d -]{8,}", "[REDACTED PHONE]", content)
                return content.strip()
        
        if cached_result:
            print(f"CACHE HIT! Similarity: {cached_result.get('similarity', 'N/A')},{cached_result['response']} ")
            formatted_context = sanitize_kb_content(cached_result.get("response", ""))
            state["context"] = f"A similar query was resolved in the past.\nCached Response: {formatted_context}"
            state["steps_taken"].append("cache_hit")
            analytics_service.log_event('cache_hit', {'category': state.get('category')}) # Added
        else:
            print(f"CACHE MISS for ticket {state['ticket_id']}")
            state["context"] = None # Explicitly set to None for the conditional edge
            state["steps_taken"].append("cache_miss")
        return state

    # --- NEW NODE FOR CONDITIONAL QUERY REWRITING ---
    async def rewrite_query_for_retrieval(self, state: GraphState) -> GraphState:
        """Conditionally rewrites the query for specific categories to improve retrieval."""
        print("EVALUATING QUERY FOR REWRITING", state["category"])
        category = state["category"]
        original_query = state["original_query"]

        kb_category = self._get_kb_category(category)

        # Only rewrite for the specified categories
        if kb_category not in ["curriculum_documents", "program_details_documents"]:
            print(f"Category '{kb_category}' does not require query rewriting. Using original query.")
            state["rewritten_query"] = original_query
            state["steps_taken"].append("rewrite_skipped")
            return state

        print(f"REWRITING QUERY for category: {category}")

        if kb_category == "curriculum_documents":
            prompt_text = """You are an expert search query creator. Your task is to rewrite a user's question into a highly effective search query optimized for a technical curriculum knowledge base.
            Focus on extracting key technical terms, programming concepts, library names, or algorithm names. The query should be concise and keyword-driven.
            
            User question: {query}
            
            Respond with a single, optimized 
         query."""
        else: # program_details_documents
            prompt_text = """You are an expert search query creator. Your task is to rewrite a user's question into a highly effective search query optimized for a program policy, timeline and FAQ knowledge base.
            Focus on extracting keywords in the query. If the user query is not in proper english, understand the query and respond with an effective search query in english with keywords.
            
            User question: {query}
            
            Respond with a single, optimized search query."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_text),
            ("human", "Rewrite the following user question: {query}")
        ])
        
        rewriter_chain = prompt | self.query_rewriter_llm.with_structured_output(RewrittenQuery)

        try:
            result = await rewriter_chain.ainvoke({"query": original_query})
            rewritten = result.rewritten_query
            print(f"Original Query: '{original_query}'")
            print(f"Rewritten Query: '{rewritten}'")
            state["rewritten_query"] = rewritten
            state["steps_taken"].append("query_rewritten")
            print(f"Query successfully rewritten for category:", state["rewritten_query"])
        except Exception as e:
            print(f"REWRITING ERROR: {e}. Falling back to original query.")
            state["rewritten_query"] = original_query
            state["error_message"
                  ] = f"Query rewriting failed: {e}"

        return state


    async def retrieve_context(self, state: GraphState) -> GraphState:
        """Retrieve context using the RetrieverAgent on cache miss."""
        print(f"RETRIEVING CONTEXT for ticket {state['ticket_id']}")
        try:
            print(f"retreive context: {state.get('category')}")
            retriever_result = await self.retriever_agent.process({
                "original_query": state["original_query"],
                "category": state["category"],
                "ticket_id": state["ticket_id"],
                "rewritten_query": state.get("rewritten_query", state["original_query"]),
                "user_course_category": state.get("user_course_category"),
                "user_course_name": state.get("user_course_name")
            })
            retrieved_docs = retriever_result.get("retrieved_context", [])
            
            def sanitize_kb_content(content: str) -> str:
                # Remove greetings, closings, personal names, phone numbers
                content = re.sub(r"Dear .*?,", "", content)
                content = re.sub(r"Thanks.*", "", content, flags=re.IGNORECASE | re.DOTALL)
                content = re.sub(r"\+?\d[\d -]{8,}", "[REDACTED PHONE]", content)
                return content.strip()
            
            if not retrieved_docs:
                state["context"] = "No relevant documents were found in the knowledge base."
            else:
                formatted_context = "\n---\n".join([
                    f"Source: {doc.get('filename', 'N/A')}\nNotes: {sanitize_kb_content(doc.get('content', ''))}"
                    for doc in retrieved_docs
                ])
                state["context"] = formatted_context
            
            state["steps_taken"].append("context_retrieved")
            return state
        except Exception as e:
            print(f"RETRIEVAL ERROR: {e}")
            state["error_message"] = f"Context retrieval failed: {str(e)}"
            state["context"] = "An error occurred while retrieving context."
            return state

    async def generate_and_decide(self, state: GraphState) -> GraphState:
        """Generate a response or decide on the next action in a single step."""
        print(f"GENERATE AND DECIDE for ticket {state['ticket_id']}, {state['messages']}")

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a support expert for Masai School.
Your task is to analyze the student's query along witht title and available context to make a single, definitive decision.

IMPORTANT:
- The KB context contains fragments from past cases.  
- They may be outdated or irrelevant.  
- You must synthesize a **new** answer in your own words.  
- Direct reuse of sentences, greetings, names, or structure is prohibited.  
- If your answer is more than 50% similar to the KB snippet, it will be rejected.
- Your tone must remain polite, supportive, and consistent with Masai’s style.


**Decision Logic:**
1. **Classify Team:** First, determine if the query is for **EC (Experience Champion)** or **IA (Instructor Associate)**.
   * EC: Logistics, lecures, submissions, approvals, platform related, attendance, leave, evaluations, placements, finances (ISA/NBFC), non-technical queries.
   * IA: Academic doubts, coding, DSA, code reviews.

2. **Choose One Action:**
   a. **request_info:** If the query lacks specific details needed for a full answer (e.g., missing dates, specifics of a bug), choose this. You MUST list the needed info in `missing_info`.
   b. **escalate:** If the query is too complex, sensitive, or requires a manual action you can't perform, choose this. You MUST provide a clear `escalation_reason`.
   c. **respond:** If you have enough context to fully and accurately answer, choose this. You MUST generate a helpful and complete `response` in your own words Do not claim things you are not completely sure about.

**Note:**
1. Note that for students you are the EC or IA. They do not know you are an agent so form your response statement accordingly. While escalating either say we'll get back shortly or sent to relevant authority for resolving.
2. In case student is required to submit or share any documents or information, consider choosing request_info if it is appropriate for the situation.
3. If student has given any supporting documents or information which needs to be checked and confirmed by admin, consider choosing escalate.

**Output Format:**
Respond ONLY with 1 valid JSON object matching the `AgentDecision` schema as follows. Do not add explanations or markdown or any Markdown fences (```json ...``` or ```).
IMPORTANT: Output must be exactly one JSON object. 
Do not repeat the JSON object or KEY - VALUES in the object. 
Do not output multiple decision objects. 
If you output anything else, it will cause a system error.
{{
  "decision": "respond" | "request_info" | "escalate",
  "response": "Your generated response here.", // Must be rewritten in your own words, no direct copy from KB, Start the response with a sweet message like "Dear student, 
Thank you for reaching out to us. Supporting our students is our highest priority. 😊" and end it with "Thanks and Regards.". DO NOT INCLUDE personal details of any person like name, contact, etc. 
  "missing_info": ["List of questions or items needed. Null if not applicable."],
  "escalation_reason": "Reason for escalation. Null if not applicable.",
  "admin_type": "EC" | "IA",
  "confidence": "Your confidence score with respect to the decision and response in the range [0.0, 1.0]. Must be a float."
}}
"""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", """I am giving you knowledge base context and user query to help you make a decision. You may refer to the knowledge base context for facts, dates, and procedures.
             Also you may understand Masai's style from it and generate your response similarly.
             DO NOT USE IT VERBATIM. Must be rewritten in your own words.
             Knowledge base context may be of 2 types:
             1. Previously resolved tickets for reference - DO NOT COPY THE CONTENT, consider that the information might be old and currently irrelevant. Generate your decision and response accordingly. Do not promise or claim to do anything that you do not have the capacity or authority to do. Escalate the ticket to admin instead.
             2. Program and Curriculum details - for course related queries, you can use this information to generate your response.
**Available Knowledge Base Context :**
{context}

**Query Title:**
{title}

**Current User Query:**
{query}

Also go through message history, if any, to understand the complete situation.

Make your decision.
""")
        ])
        
        chain = prompt | self.llm
        try:
            result = await chain.ainvoke({
                "messages": state["messages"],
                "context": state["context"],
                "title": state["title"],
                "query": state["original_query"]
            })
            
            raw = result.content.strip()
            print(f"LLM ROUTING RESPONSE (raw):\n{raw}\n")

            # 1. Strip any Markdown fences (```json ...``` or ```)
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else parts[0]
                if raw.startswith("json\n"):
                    raw = raw[5:]

            # 2. Extract the first {...} block in case there’s any trailing text
            # re.DOTALL ensures '.' matches newlines
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                json_str = raw
            
            decision_json = json.loads(json_str)
            
            # Validate with Pydantic
            agent_decision = AgentDecision(**decision_json)
            state["agent_decision"] = agent_decision.model_dump()
            print(f"Decision: {state['agent_decision']['decision']}, Team: {state['agent_decision']['admin_type']}")

        except Exception as e:
            print(f"GENERATE/DECIDE ERROR: {e}\nContent was: {getattr(result, 'content', 'N/A')}")
            traceback.print_exc()
            state["error_message"] = f"LLM decision failed: {str(e)}"
            # Fallback to a safe escalation
            state["agent_decision"] = {
                "decision": "escalate", "escalation_reason": "AI agent encountered a processing error.",
                "admin_type": "EC", "confidence": 0.0, "response": None, "missing_info": None
            }
        
        state["steps_taken"].append("decision_made")
        return state

    async def finalize_and_act(self, state: GraphState) -> GraphState:
        """Executes the decision made by the agent and updates the ticket."""
        print(f"FINALIZING ticket {state['ticket_id']}")
        try:
            decision = state.get("agent_decision")
            ticket_id = state["ticket_id"]
            category = state.get("category") # Added

            if not decision:
                raise ValueError("Agent decision not found in state, cannot finalize.")

            action = decision.get("decision").lower().replace(" ", "_")
            confidence = float(decision.get("confidence", 0.0))

            # Outcome 1: Request more information from the student
            if action == 'request_info' and decision.get('missing_info'):
                print("Action: Requesting info from student.", decision.get("admin_type", "EC"), {state['agent_decision']['admin_type']})
                message = ( decision.get("response") or "Thank you for contacting us. To better assist you, could you please provide the following information?\n\n" + "\n".join(f"• {info}" for info in decision.get("missing_info", [])))                
                print("msg adding to conversaion:", message, decision.get('response'))
                conversation_service.create_conversation(ticket_id, "agent", message, confidence_score=confidence)
                
                admin = await self._find_available_admin(decision.get("admin_type", "EC"))
                print(f"admin in request info {admin}.")
                admin_id = admin["id"] if admin else None
                print(f"assigning admin in request info {admin_id}.")
                ticket_service.update_ticket_status(ticket_id, TicketStatus.STUDENT_ACTION_REQUIRED.value, admin_id)
                state["final_status"] = TicketStatus.STUDENT_ACTION_REQUIRED.value

            # Outcome 2: Escalate to a human admin
            elif action == 'escalate':
                print(f"Action: Escalating to human admin ({decision.get('admin_type')}).")
                analytics_service.log_event('escalated', {'category': category})
                await self.escalation_agent.process({
                    "ticket_id": ticket_id, "admin_type": decision.get("admin_type", "EC"),
                    "response": decision.get("response", "")
                })
                state["final_status"] = TicketStatus.ADMIN_ACTION_REQUIRED.value

            # Outcome 3: Respond to the student and resolve the ticket
            elif action == 'respond' and decision.get('response'):
                print("Action: Responding and resolving ticket.",decision.get("admin_type", "EC"), )
                response = decision['response']
                analytics_service.log_event('agent_resolved', {'category': category, 'confidence': confidence}) # Added
                conversation_service.create_conversation(ticket_id, "agent", response, confidence_score=confidence * 100) # Modified
                ticket_service.update_ticket_status(ticket_id, TicketStatus.RESOLVED.value)
                state["final_status"] = TicketStatus.RESOLVED.value

                if confidence >= 0.85 and "cache_miss" in state["steps_taken"]:
                    await self.cache_service.store_response(query=state["original_query"], 
                        response=response, 
                        confidence=confidence, 
                        category=state["category"],
                        metadata={
                            "course_category": state.get("user_course_category"),
                            "course_names": [state.get("user_course_name")] if state.get("user_course_name") else []
                        })
                    print("Stored successful response in cache.")
            
            else:
                raise ValueError(f"Invalid or incomplete agent decision: {action}")

        except Exception as e:
            print(f"FINALIZATION ERROR: {e}")
            traceback.print_exc()
            state["error_message"] = f"Finalization failed: {str(e)}"
            # Safe fallback: escalate the ticket
            analytics_service.log_event('escalated', {'category': state.get('category'), 'reason': 'finalization_error'}) # Added
            await self.escalation_agent.process({"ticket_id": state["ticket_id"], "admin_type": "EC"})
            state["final_status"] = TicketStatus.ADMIN_ACTION_REQUIRED.value

        state["steps_taken"].append(f"finalized_as_{state['final_status']}")
        return state
    
    async def process_ticket(self, ticket_id: str):
        """Main entry point to process a ticket through the workflow."""
        print(f"\n--- STARTING WORKFLOW for ticket {ticket_id} ---")
        initial_state = GraphState(ticket_id=ticket_id)
        try:
            final_state = await self.workflow.ainvoke(initial_state)
            print(f"--- WORKFLOW COMPLETED for ticket {ticket_id}: Final Status = {final_state.get('final_status')} ---")
            return final_state
        except Exception as e:
            print(f"--- WORKFLOW EXECUTION ERROR for ticket {ticket_id}: {e} ---")
            traceback.print_exc()
            raise

# Export for use in other modules
workflow_instance = EnhancedLangGraphWorkflow()

async def process_ticket_async(ticket_id: str):
    """Async wrapper for background task execution."""
    print(f"Processing ticket {ticket_id} through LangGraph workflow...")
    await workflow_instance.process_ticket(ticket_id)