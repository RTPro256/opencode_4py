"""
Graph RAG Implementation.

Graph-based RAG for entity relationships and community detection.
Integrated from OpenRAG's GraphRAG implementation.

The Graph RAG approach:
1. Extract entities from documents
2. Build knowledge graph
3. Detect communities
4. Generate community summaries
5. Answer using graph context
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

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


@dataclass
class Entity:
    """An entity in the knowledge graph."""
    name: str
    entity_type: str
    description: str = ""
    mentions: int = 1


@dataclass
class Relationship:
    """A relationship between entities."""
    source: str
    target: str
    relation_type: str
    description: str = ""
    weight: float = 1.0


@dataclass
class Community:
    """A community of related entities."""
    id: str
    entities: Set[str]
    summary: str = ""
    key_entities: List[str] = field(default_factory=list)


class GraphRAGConfig(RAGMethodConfig):
    """Configuration specific to Graph RAG."""
    
    # Graph RAG specific settings
    max_entities: int = 1000
    max_relationships: int = 5000
    community_detection: bool = True
    min_community_size: int = 3
    entity_types: List[str] = field(default_factory=lambda: [
        "PERSON", "ORGANIZATION", "LOCATION", "CONCEPT", "EVENT"
    ])


class GraphRAG(BaseRAGMethod):
    """
    Graph RAG implementation.
    
    Graph RAG improves retrieval by:
    1. Building a knowledge graph from documents
    2. Detecting communities of related entities
    3. Generating summaries for communities
    4. Using graph structure for context
    
    Based on OpenRAG's GraphRagAgent and Microsoft's GraphRAG.
    
    Reference: "From Local to Global: A Graph RAG Approach to Query-Focused Summarization"
    https://arxiv.org/abs/2404.16130
    """
    
    method_name = "graph"
    method_description = "Graph-based RAG with entity relationships"
    
    ENTITY_EXTRACTION_PROMPT = """Extract entities and relationships from the following text.

Text: {text}

Extract:
1. Entities (with type: PERSON, ORGANIZATION, LOCATION, CONCEPT, EVENT)
2. Relationships between entities

Format your response as:
ENTITIES:
- EntityName (TYPE): brief description

RELATIONSHIPS:
- Entity1 -> RELATION -> Entity2: description

Response:"""
    
    COMMUNITY_SUMMARY_PROMPT = """Summarize the following community of related entities.

Entities: {entities}

Provide a concise summary of what this community represents and how the entities are related.

Summary:"""
    
    def __init__(
        self,
        config: Optional[RAGMethodConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Initialize Graph RAG.
        
        Args:
            config: Configuration for the RAG method
            embedding_provider: Provider for embeddings
            vector_store: Vector store for document storage
            llm_provider: Provider for LLM generation
        """
        super().__init__(
            config=config or GraphRAGConfig(),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            llm_provider=llm_provider,
        )
        
        # Graph storage
        self._documents: List[RetrievedDocument] = []
        self._entities: Dict[str, Entity] = {}
        self._relationships: List[Relationship] = []
        self._communities: Dict[str, Community] = {}
        self._entity_to_doc: Dict[str, List[str]] = {}
    
    async def query(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RAGResult:
        """
        Execute a Graph RAG query.
        
        Args:
            question: The question to answer
            context: Optional context for the query
            
        Returns:
            RAGResult containing the answer and sources
        """
        logger.info(f"Processing Graph RAG query: {question[:100]}...")
        
        # Step 1: Extract entities from question
        question_entities = await self._extract_entities_from_text(question)
        
        # Step 2: Find relevant documents via entity matching
        relevant_docs = self._find_documents_by_entities(question_entities)
        
        # Step 3: Find relevant communities
        relevant_communities = self._find_relevant_communities(question_entities)
        
        # Step 4: Build context from graph
        graph_context = self._build_graph_context(
            question_entities,
            relevant_docs,
            relevant_communities,
        )
        
        # Step 5: Generate answer
        answer = await self._generate_answer(question, graph_context)
        
        return RAGResult(
            answer=answer,
            sources=relevant_docs[:self.config.top_k],
            confidence=self._calculate_confidence(relevant_docs),
            metadata={
                "method": self.method_name,
                "entities_found": len(question_entities),
                "communities_matched": len(relevant_communities),
            },
        )
    
    async def index_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """
        Index documents and build knowledge graph.
        
        Args:
            documents: List of document texts
            metadata: Optional metadata for each document
            ids: Optional IDs for each document
            
        Returns:
            Number of documents indexed
        """
        import uuid
        
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        if metadata is None:
            metadata = [{} for _ in documents]
        
        # Process each document
        for i, doc in enumerate(documents):
            doc_id = ids[i]
            
            # Store document
            self._documents.append(RetrievedDocument(
                content=doc,
                source=metadata[i].get("source"),
                title=metadata[i].get("title"),
                metadata={**metadata[i], "doc_id": doc_id},
            ))
            
            # Extract entities and relationships
            await self._process_document_for_graph(doc_id, doc)
        
        # Detect communities
        if isinstance(self.config, GraphRAGConfig) and self.config.community_detection:
            await self._detect_communities()
        
        return len(documents)
    
    async def _process_document_for_graph(
        self,
        doc_id: str,
        text: str,
    ) -> None:
        """
        Process a document to extract entities and relationships.
        
        Args:
            doc_id: Document ID
            text: Document text
        """
        if not self.llm_provider:
            # Simple entity extraction without LLM
            self._simple_entity_extraction(doc_id, text)
            return
        
        prompt = self.ENTITY_EXTRACTION_PROMPT.format(text=text[:2000])
        
        response = await self.llm_provider.generate(
            prompt,
            temperature=0.0,
        )
        
        # Parse entities and relationships
        self._parse_extraction_response(doc_id, response)
    
    def _simple_entity_extraction(
        self,
        doc_id: str,
        text: str,
    ) -> None:
        """Simple entity extraction using capitalization heuristics."""
        import re
        
        # Find capitalized phrases as potential entities
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.findall(pattern, text)
        
        for match in matches:
            if len(match) > 2:  # Skip short matches
                entity_name = match.strip()
                
                if entity_name not in self._entities:
                    self._entities[entity_name] = Entity(
                        name=entity_name,
                        entity_type="UNKNOWN",
                    )
                else:
                    self._entities[entity_name].mentions += 1
                
                # Track document
                if entity_name not in self._entity_to_doc:
                    self._entity_to_doc[entity_name] = []
                if doc_id not in self._entity_to_doc[entity_name]:
                    self._entity_to_doc[entity_name].append(doc_id)
    
    def _parse_extraction_response(
        self,
        doc_id: str,
        response: str,
    ) -> None:
        """Parse entity extraction response."""
        lines = response.strip().split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if "ENTITIES:" in line:
                current_section = "entities"
                continue
            elif "RELATIONSHIPS:" in line:
                current_section = "relationships"
                continue
            
            if not line or line.startswith("-"):
                continue
            
            if current_section == "entities":
                # Parse: EntityName (TYPE): description
                if "(" in line and ")" in line:
                    try:
                        name_part, rest = line.split("(", 1)
                        entity_type, desc_part = rest.split(")", 1)
                        
                        entity_name = name_part.strip().lstrip("- ")
                        entity_type = entity_type.strip()
                        description = desc_part.lstrip(": ").strip()
                        
                        if entity_name not in self._entities:
                            self._entities[entity_name] = Entity(
                                name=entity_name,
                                entity_type=entity_type,
                                description=description,
                            )
                        else:
                            self._entities[entity_name].mentions += 1
                        
                        if entity_name not in self._entity_to_doc:
                            self._entity_to_doc[entity_name] = []
                        if doc_id not in self._entity_to_doc[entity_name]:
                            self._entity_to_doc[entity_name].append(doc_id)
                    except ValueError:
                        pass
            
            elif current_section == "relationships":
                # Parse: Entity1 -> RELATION -> Entity2
                if "->" in line:
                    try:
                        parts = line.split("->")
                        if len(parts) >= 3:
                            source = parts[0].strip().lstrip("- ")
                            relation = parts[1].strip()
                            target = parts[2].split(":")[0].strip()
                            
                            self._relationships.append(Relationship(
                                source=source,
                                target=target,
                                relation_type=relation,
                            ))
                    except (ValueError, IndexError):
                        pass
    
    async def _detect_communities(self) -> None:
        """Detect communities using simple clustering."""
        # Simple community detection based on shared documents
        entity_docs: Dict[str, Set[str]] = {}
        
        for entity, docs in self._entity_to_doc.items():
            entity_docs[entity] = set(docs)
        
        # Group entities that share documents
        community_id = 0
        processed: Set[str] = set()
        
        for entity1, docs1 in entity_docs.items():
            if entity1 in processed:
                continue
            
            community_entities = {entity1}
            processed.add(entity1)
            
            for entity2, docs2 in entity_docs.items():
                if entity2 in processed:
                    continue
                
                # If entities share documents, they're in same community
                if docs1 & docs2:
                    community_entities.add(entity2)
                    processed.add(entity2)
            
            if len(community_entities) >= 3:  # Min community size
                comm_id = f"community_{community_id}"
                self._communities[comm_id] = Community(
                    id=comm_id,
                    entities=community_entities,
                    key_entities=list(community_entities)[:5],
                )
                community_id += 1
    
    async def _extract_entities_from_text(
        self,
        text: str,
    ) -> List[str]:
        """Extract entities from text."""
        found_entities = []
        
        for entity_name in self._entities:
            if entity_name.lower() in text.lower():
                found_entities.append(entity_name)
        
        return found_entities
    
    def _find_documents_by_entities(
        self,
        entities: List[str],
    ) -> List[RetrievedDocument]:
        """Find documents that contain the given entities."""
        doc_scores: Dict[str, int] = {}
        
        for entity in entities:
            if entity in self._entity_to_doc:
                for doc_id in self._entity_to_doc[entity]:
                    doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1
        
        # Sort by score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get documents
        result = []
        for doc_id, _ in sorted_docs[:self.config.top_k * 2]:
            for doc in self._documents:
                if doc.metadata.get("doc_id") == doc_id:
                    result.append(doc)
                    break
        
        return result
    
    def _find_relevant_communities(
        self,
        entities: List[str],
    ) -> List[Community]:
        """Find communities that contain the given entities."""
        relevant = []
        
        for community in self._communities.values():
            overlap = len(set(entities) & community.entities)
            if overlap > 0:
                relevant.append(community)
        
        return relevant
    
    def _build_graph_context(
        self,
        entities: List[str],
        documents: List[RetrievedDocument],
        communities: List[Community],
    ) -> str:
        """Build context from graph structure."""
        parts = []
        
        # Add entity information
        if entities:
            entity_info = ["Related Entities:"]
            for entity_name in entities[:10]:
                if entity_name in self._entities:
                    entity = self._entities[entity_name]
                    entity_info.append(
                        f"- {entity.name} ({entity.entity_type}): {entity.description}"
                    )
            parts.append("\n".join(entity_info))
        
        # Add relationship information
        relevant_rels = [
            r for r in self._relationships
            if r.source in entities or r.target in entities
        ]
        if relevant_rels:
            rel_info = ["Relationships:"]
            for rel in relevant_rels[:10]:
                rel_info.append(
                    f"- {rel.source} --[{rel.relation_type}]--> {rel.target}"
                )
            parts.append("\n".join(rel_info))
        
        # Add document content
        if documents:
            doc_info = ["Source Documents:"]
            for i, doc in enumerate(documents[:5]):
                doc_info.append(f"\n[Document {i+1}]\n{doc.content[:500]}")
            parts.append("\n".join(doc_info))
        
        return "\n\n".join(parts)
    
    async def _generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """Generate an answer using the LLM."""
        prompt = f"""Based on the following knowledge graph context, please answer the question.

Context:
{context}

Question: {question}

Please provide a clear and accurate answer based on the provided context.

Answer:"""
        
        if self.llm_provider:
            return await self.llm_provider.generate(
                prompt,
                temperature=self.config.temperature,
            )
        else:
            return f"Based on the knowledge graph:\n\n{context}"
    
    def _calculate_confidence(self, sources: List[RetrievedDocument]) -> float:
        """Calculate confidence score."""
        if not sources:
            return 0.0
        
        # Higher confidence if more entities matched
        base_confidence = min(len(sources) / self.config.top_k, 1.0)
        return base_confidence * 0.8
