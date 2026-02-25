"""
Agentic RAG Implementation.

Agent-based RAG with tool use and iterative reasoning.
Integrated from OpenRAG's AgenticRAG implementation.

The Agentic RAG approach:
1. Agent analyzes query and plans retrieval
2. Uses tools (search, retrieve, etc.)
3. Iteratively refines based on results
4. Generates comprehensive answer
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .base import (
    BaseRAGMethod,
    EmbeddingProvider,
    LLMProvider,
    RAGMethodConfig,
    RAGResult,
    RetrievedDocument,
    VectorStore,
)

logger = logging.getLogger(__name__)


class AgentAction(str, Enum):
    """Actions the agent can take."""
    SEARCH = "search"
    RETRIEVE = "retrieve"
    REFINE = "refine"
    ANSWER = "answer"
    GIVE_UP = "give_up"


@dataclass
class AgentStep:
    """A single step in the agent's reasoning."""
    action: AgentAction
    input: str
    output: str
    reasoning: str = ""


class AgenticRAGConfig(RAGMethodConfig):
    """Configuration specific to Agentic RAG."""
    
    # Agentic specific settings
    max_iterations: int = 5
    reflection_enabled: bool = True
    tool_use_enabled: bool = True
    planning_enabled: bool = True


class AgenticRAG(BaseRAGMethod):
    """
    Agentic RAG implementation with tool use.
    
    Agentic RAG improves retrieval by:
    1. Using an agent to plan and execute retrieval
    2. Iteratively refining based on intermediate results
    3. Using tools for search and retrieval
    4. Self-reflection on answer quality
    
    Based on OpenRAG's AgenticRagAgent implementation.
    """
    
    method_name = "agentic"
    method_description = "Agent-based RAG with tool use and iterative reasoning"
    
    PLANNING_PROMPT = """You are a research agent. Analyze the following question and plan your approach.

Question: {question}

Available tools:
- search(query): Search for relevant documents
- retrieve(doc_id): Get specific document content

Plan your approach. What steps will you take to answer this question?

Plan:"""
    
    ACTION_PROMPT = """You are a research agent. Based on the current state, decide your next action.

Question: {question}

Previous steps:
{previous_steps}

Current knowledge:
{knowledge}

Available actions:
- SEARCH: Search for more documents (provide search query)
- ANSWER: Provide final answer (provide answer text)
- GIVE_UP: Cannot answer with available information

What is your next action? Format:
ACTION: [SEARCH/ANSWER/GIVE_UP]
INPUT: [query or answer text]
REASONING: [why this action]

Response:"""
    
    REFLECTION_PROMPT = """Evaluate the following answer for completeness and accuracy.

Question: {question}

Answer: {answer}

Sources used:
{sources}

Is this answer satisfactory? If not, what additional information is needed?

Evaluation:"""
    
    def __init__(
        self,
        config: Optional[RAGMethodConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Initialize Agentic RAG.
        
        Args:
            config: Configuration for the RAG method
            embedding_provider: Provider for embeddings
            vector_store: Vector store for document storage
            llm_provider: Provider for LLM generation
        """
        super().__init__(
            config=config or AgenticRAGConfig(),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            llm_provider=llm_provider,
        )
        
        self._documents: List[RetrievedDocument] = []
        self._tools: Dict[str, Callable] = {}
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register available tools."""
        self._tools = {
            "search": self._tool_search,
            "retrieve": self._tool_retrieve,
        }
    
    async def query(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RAGResult:
        """
        Execute an Agentic RAG query.
        
        Args:
            question: The question to answer
            context: Optional context for the query
            
        Returns:
            RAGResult containing the answer and sources
        """
        logger.info(f"Processing Agentic RAG query: {question[:100]}...")
        
        max_iterations = 5
        if isinstance(self.config, AgenticRAGConfig):
            max_iterations = self.config.max_iterations
        
        # Agent state
        steps: List[AgentStep] = []
        knowledge: List[str] = []
        sources: List[RetrievedDocument] = []
        
        # Iterative agent loop
        for iteration in range(max_iterations):
            # Decide next action
            action, action_input, reasoning = await self._decide_action(
                question, steps, knowledge
            )
            
            # Execute action
            if action == AgentAction.SEARCH:
                # Search for documents
                results = await self._tool_search(action_input)
                knowledge.extend(results["summaries"])
                sources.extend(results["documents"])
                
                steps.append(AgentStep(
                    action=action,
                    input=action_input,
                    output=f"Found {len(results['documents'])} documents",
                    reasoning=reasoning,
                ))
            
            elif action == AgentAction.ANSWER:
                # Generate final answer
                return RAGResult(
                    answer=action_input,
                    sources=sources[:self.config.top_k],
                    confidence=self._calculate_confidence(sources),
                    metadata={
                        "method": self.method_name,
                        "iterations": iteration + 1,
                        "steps": len(steps),
                    },
                )
            
            elif action == AgentAction.GIVE_UP:
                # Cannot answer
                return RAGResult(
                    answer="I was unable to find sufficient information to answer your question.",
                    sources=sources,
                    confidence=0.0,
                    metadata={
                        "method": self.method_name,
                        "failed": True,
                        "iterations": iteration + 1,
                    },
                )
        
        # Max iterations reached - generate best effort answer
        final_answer = await self._generate_best_effort_answer(question, knowledge)
        
        return RAGResult(
            answer=final_answer,
            sources=sources[:self.config.top_k],
            confidence=self._calculate_confidence(sources) * 0.7,  # Lower confidence
            metadata={
                "method": self.method_name,
                "iterations": max_iterations,
                "max_reached": True,
            },
        )
    
    async def index_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """Index documents for retrieval."""
        import uuid
        
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        if metadata is None:
            metadata = [{} for _ in documents]
        
        chunks = []
        chunk_metadata = []
        chunk_ids = []
        
        for i, doc in enumerate(documents):
            doc_chunks = self._chunk_document(doc)
            for j, chunk in enumerate(doc_chunks):
                chunks.append(chunk)
                chunk_ids.append(f"{ids[i]}_chunk_{j}")
                chunk_metadata.append({
                    **metadata[i],
                    "parent_doc_id": ids[i],
                    "chunk_index": j,
                })
        
        if self.vector_store and self.embedding_provider:
            embeddings = await self.embedding_provider.embed_texts(
                chunks,
                model=self.config.embedding_model,
            )
            await self.vector_store.add_documents(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=chunks,
                metadata=chunk_metadata,
            )
        else:
            for i, chunk in enumerate(chunks):
                self._documents.append(RetrievedDocument(
                    content=chunk,
                    source=chunk_metadata[i].get("source"),
                    title=chunk_metadata[i].get("title"),
                    metadata=chunk_metadata[i],
                ))
        
        return len(documents)
    
    async def _decide_action(
        self,
        question: str,
        steps: List[AgentStep],
        knowledge: List[str],
    ) -> tuple[AgentAction, str, str]:
        """
        Decide the next action based on current state.
        
        Args:
            question: The question
            steps: Previous steps
            knowledge: Accumulated knowledge
            
        Returns:
            Tuple of (action, input, reasoning)
        """
        if not self.llm_provider:
            return self._heuristic_action(question, steps, knowledge)
        
        # Format previous steps
        steps_text = "\n".join(
            f"- {s.action.value}: {s.input} -> {s.output}"
            for s in steps[-3:]  # Last 3 steps
        ) or "None"
        
        # Format knowledge
        knowledge_text = "\n".join(knowledge[-5:]) or "None"
        
        prompt = self.ACTION_PROMPT.format(
            question=question,
            previous_steps=steps_text,
            knowledge=knowledge_text,
        )
        
        response = await self.llm_provider.generate(
            prompt,
            temperature=0.0,
        )
        
        return self._parse_action_response(response)
    
    def _heuristic_action(
        self,
        question: str,
        steps: List[AgentStep],
        knowledge: List[str],
    ) -> tuple[AgentAction, str, str]:
        """Simple heuristic-based action selection."""
        # If no searches yet, search
        search_steps = [s for s in steps if s.action == AgentAction.SEARCH]
        
        if len(search_steps) == 0:
            return (
                AgentAction.SEARCH,
                question,
                "Initial search for relevant documents",
            )
        
        # If we have knowledge, try to answer
        if len(knowledge) >= 2:
            return (
                AgentAction.ANSWER,
                f"Based on the retrieved information: {' '.join(knowledge[:3])}",
                "Sufficient information gathered",
            )
        
        # Otherwise, search more
        return (
            AgentAction.SEARCH,
            f"more details about {question}",
            "Need more information",
        )
    
    def _parse_action_response(
        self,
        response: str,
    ) -> tuple[AgentAction, str, str]:
        """Parse action from LLM response."""
        action = AgentAction.SEARCH
        action_input = ""
        reasoning = ""
        
        lines = response.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if line.startswith("ACTION:"):
                action_str = line.split(":", 1)[1].strip().upper()
                if "SEARCH" in action_str:
                    action = AgentAction.SEARCH
                elif "ANSWER" in action_str:
                    action = AgentAction.ANSWER
                elif "GIVE" in action_str:
                    action = AgentAction.GIVE_UP
            elif line.startswith("INPUT:"):
                action_input = line.split(":", 1)[1].strip()
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
        
        return action, action_input, reasoning
    
    async def _tool_search(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """
        Search tool for finding documents.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with documents and summaries
        """
        if self.vector_store and self.embedding_provider:
            query_embedding = await self.embedding_provider.embed_query(
                query,
                model=self.config.embedding_model,
            )
            docs = await self.vector_store.search(
                query_embedding,
                top_k=self.config.top_k,
            )
        else:
            docs = self._keyword_search(query)
        
        # Create summaries
        summaries = [doc.content[:200] + "..." for doc in docs]
        
        return {
            "documents": docs,
            "summaries": summaries,
        }
    
    async def _tool_retrieve(
        self,
        doc_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve tool for getting specific document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Dictionary with document content
        """
        for doc in self._documents:
            if doc.metadata.get("doc_id") == doc_id:
                return {"content": doc.content, "document": doc}
        
        return {"content": "Document not found", "document": None}
    
    def _keyword_search(self, query: str) -> List[RetrievedDocument]:
        """Simple keyword-based search fallback."""
        query_terms = set(query.lower().split())
        scored_docs = []
        
        for doc in self._documents:
            doc_terms = set(doc.content.lower().split())
            overlap = len(query_terms & doc_terms)
            if overlap > 0:
                score = overlap / len(query_terms)
                scored_docs.append((score, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:self.config.top_k]]
    
    def _chunk_document(self, document: str) -> List[str]:
        """Chunk a document into smaller pieces."""
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        if len(document) <= chunk_size:
            return [document]
        
        chunks = []
        start = 0
        
        while start < len(document):
            end = start + chunk_size
            chunk = document[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap if end < len(document) else end
        
        return chunks
    
    async def _generate_best_effort_answer(
        self,
        question: str,
        knowledge: List[str],
    ) -> str:
        """Generate best effort answer from accumulated knowledge."""
        if not knowledge:
            return "I was unable to find relevant information."
        
        context = "\n\n".join(knowledge)
        
        if self.llm_provider:
            prompt = f"""Based on the following information, provide the best possible answer to the question.

Information:
{context}

Question: {question}

Answer:"""
            
            return await self.llm_provider.generate(
                prompt,
                temperature=self.config.temperature,
            )
        else:
            return f"Based on the retrieved information:\n\n{context}"
    
    def _calculate_confidence(self, sources: List[RetrievedDocument]) -> float:
        """Calculate confidence score."""
        if not sources:
            return 0.0
        
        avg_score = sum(s.score for s in sources) / len(sources) if sources else 0
        return min(max(avg_score, 0.0), 1.0)
