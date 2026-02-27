"""
ArXiv Research Agent

Downloads and analyzes papers from arXiv with innovation scoring.
Based on Locally-Hosted-LM-Research-Assistant implementation.
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import arxiv
try:
    import arxiv
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False
    arxiv = None

# Try to import pymupdf
try:
    import fitz  # pymupdf
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None


class PaperInfo(BaseModel):
    """Information about an arXiv paper"""
    arxiv_id: str = Field(..., description="arXiv paper ID")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    summary: str = Field("", description="Paper abstract/summary")
    pdf_url: str = Field("", description="URL to PDF")
    published: str = Field("", description="Publication date")
    categories: List[str] = Field(default_factory=list, description="arXiv categories")
    innovation_score: Optional[int] = Field(None, description="Innovation score (1-10)")
    analysis: Optional[str] = Field(None, description="LLM analysis of the paper")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": self.authors,
            "summary": self.summary,
            "pdf_url": self.pdf_url,
            "published": self.published,
            "categories": self.categories,
            "innovation_score": self.innovation_score,
            "analysis": self.analysis,
        }


class ArxivAgent:
    """
    Downloads and analyzes papers from arXiv with innovation scoring.
    
    Innovation scoring (1-10) based on:
    - Novelty of approach
    - Uniqueness of contribution
    - Potential impact
    - Technical depth
    """
    
    def __init__(
        self,
        download_dir: str = "./arxiv_papers",
        llm_client: Optional[Any] = None,
    ):
        """
        Initialize the ArXiv agent.
        
        Args:
            download_dir: Directory to store downloaded papers
            llm_client: LLM client for paper analysis (optional)
        """
        if not ARXIV_AVAILABLE:
            raise ImportError("arxiv package not installed. Install with: pip install arxiv")
        
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.llm_client = llm_client
    
    def search_papers(
        self,
        query: str,
        max_results: int = 5,
        sort_by: str = "relevance",
    ) -> List[PaperInfo]:
        """
        Search arXiv for papers.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            sort_by: Sort criterion (relevance, lastUpdatedDate, submittedDate)
            
        Returns:
            List of PaperInfo objects
        """
        try:
            sort_criterion = {
                "relevance": arxiv.SortCriterion.Relevance,
                "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
                "submittedDate": arxiv.SortCriterion.SubmittedDate,
            }.get(sort_by, arxiv.SortCriterion.Relevance)
            
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_criterion,
            )
            
            papers = []
            for result in search.results():
                paper = PaperInfo(
                    arxiv_id=result.entry_id.split('/')[-1],
                    title=result.title,
                    authors=[a.name for a in result.authors],
                    summary=result.summary,
                    pdf_url=result.pdf_url,
                    published=str(result.published),
                    categories=list(result.categories),
                )
                papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers for query: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []
    
    def download_paper(self, arxiv_id: str) -> Optional[Path]:
        """
        Download PDF of a paper.
        
        Args:
            arxiv_id: arXiv paper ID
            
        Returns:
            Path to downloaded PDF or None on failure
        """
        try:
            # Clean the arxiv_id
            match = re.search(r'\d{4}\.\d{4,5}(?:v\d+)?', arxiv_id)
            clean_id = match.group(0) if match else arxiv_id
            
            logger.info(f"Downloading paper: {clean_id}")
            paper = next(arxiv.Search(id_list=[clean_id]).results())
            pdf_path = self.download_dir / f"{clean_id.replace('/', '_')}.pdf"
            paper.download_pdf(filename=str(pdf_path))
            
            logger.info(f"Downloaded: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def extract_text(self, pdf_path: Path, max_chars: int = 6000) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            max_chars: Maximum characters to extract
            
        Returns:
            Extracted text
        """
        if not PYMUPDF_AVAILABLE:
            raise ImportError("pymupdf not installed. Install with: pip install pymupdf")
        
        try:
            doc = fitz.open(str(pdf_path))
            text = ""
            for page in doc:
                text += page.get_text("text")
            
            # Limit text to avoid crashing the LLM
            if len(text) > max_chars:
                half = max_chars // 2
                text = text[:half] + "\n\n[... middle section omitted ...]\n\n" + text[-half:]
            
            return text
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""
    
    def analyze_paper(
        self,
        arxiv_id: str,
        include_score: bool = True,
    ) -> Optional[PaperInfo]:
        """
        Download and analyze a paper.
        
        Args:
            arxiv_id: arXiv paper ID
            include_score: Whether to include innovation scoring
            
        Returns:
            PaperInfo with analysis or None on failure
        """
        pdf_path = self.download_paper(arxiv_id)
        if not pdf_path:
            return None
        
        text = self.extract_text(pdf_path)
        if not text:
            return None
        
        # Get paper metadata
        papers = self.search_papers(arxiv_id, max_results=1)
        if not papers:
            return None
        
        paper = papers[0]
        
        # Analyze with LLM if available
        if self.llm_client:
            analysis = self._analyze_with_llm(text, include_score)
            paper.analysis = analysis.get("analysis")
            paper.innovation_score = analysis.get("score")
        
        return paper
    
    def _analyze_with_llm(self, text: str, include_score: bool) -> Dict[str, Any]:
        """Analyze paper text with LLM"""
        if not self.llm_client:
            return {"analysis": None, "score": None}
        
        score_prompt = """
        Rate the innovation of this paper on a scale of 1-10 based on:
        - Novelty of approach (1-10)
        - Uniqueness of contribution (1-10)
        - Potential impact (1-10)
        - Technical depth (1-10)
        
        Return only the average score as a single integer.
        """ if include_score else ""
        
        prompt = f"""Analyze this research paper and provide:
        1. A concise summary (3-5 sentences)
        2. Key contributions
        3. Methodology overview
        4. Main findings
        5. Limitations
        {score_prompt}
        
        Paper text:
        {text}
        """
        
        try:
            # This would call the LLM client
            # Implementation depends on the LLM client interface
            response = self.llm_client.generate(prompt)
            return {"analysis": response, "score": None}
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {"analysis": None, "score": None}
