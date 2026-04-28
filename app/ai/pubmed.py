"""
PubMed Literature Search - Real NCBI E-utilities integration.

Features:
- Search PubMed for related NHANES studies
- Fetch article metadata (title, authors, journal, abstract)
- Format references in Vancouver/Lancet style
- Cache results to avoid redundant API calls
"""
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedSearch:
    """Search and retrieve literature from PubMed."""
    
    def __init__(self, api_key: str = "", email: str = ""):
        self.api_key = api_key
        self.email = email
        self._cache = {}
    
    def search(self, query: str, max_results: int = 10,
               min_year: int = 2015, article_type: str = "") -> List[Dict[str, Any]]:
        """
        Search PubMed and return formatted results.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            min_year: Minimum publication year
            article_type: Filter by article type (e.g., "Journal Article")
        """
        # Build search query
        search_query = query
        if min_year:
            search_query += f" AND {min_year}[dp]"
        if article_type:
            search_query += f" AND {article_type}[pt]"
        
        # Add NHANES filter for relevance
        if "nhanes" not in query.lower():
            search_query += " AND (NHANES OR National Health and Nutrition Examination Survey)"
        
        cache_key = f"{search_query}_{max_results}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # Step 1: Search for PMIDs
            pmids = self._esearch(search_query, max_results)
            if not pmids:
                return []
            
            # Step 2: Fetch article details
            articles = self._efetch(pmids)
            
            self._cache[cache_key] = articles
            return articles
            
        except Exception as e:
            logger.error(f"PubMed search error: {e}")
            return []
    
    def _esearch(self, query: str, retmax: int = 10) -> List[str]:
        """Search PubMed and return list of PMIDs."""
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": retmax,
            "retmode": "json",
            "sort": "relevance",
        }
        if self.api_key:
            params["api_key"] = self.api_key
        
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{PUBMED_BASE}/esearch.fcgi", params=params)
            resp.raise_for_status()
            data = resp.json()
        
        return data.get("esearchresult", {}).get("idlist", [])
    
    def _efetch(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch article details for a list of PMIDs."""
        if not pmids:
            return []
        
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }
        if self.api_key:
            params["api_key"] = self.api_key
        
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{PUBMED_BASE}/efetch.fcgi", params=params)
            resp.raise_for_status()
        
        return self._parse_xml(resp.text)
    
    def _parse_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """Parse PubMed XML response."""
        articles = []
        
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []
        
        for article_elem in root.findall(".//PubmedArticle"):
            try:
                article = self._parse_article(article_elem)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.warning(f"Error parsing article: {e}")
        
        return articles
    
    def _parse_article(self, elem) -> Optional[Dict[str, Any]]:
        """Parse a single PubmedArticle element."""
        medline = elem.find(".//MedlineCitation")
        if medline is None:
            return None
        
        pmid = medline.findtext(".//PMID", "")
        article = medline.find(".//Article")
        if article is None:
            return None
        
        # Title
        title = article.findtext(".//ArticleTitle", "")
        
        # Authors
        authors = []
        for author in article.findall(".//Author"):
            last = author.findtext("LastName", "")
            first = author.findtext("ForeName", "")
            if last:
                authors.append(f"{last} {first}".strip())
        
        # Journal
        journal_elem = article.find(".//Journal")
        journal = ""
        journal_abbrev = ""
        year = ""
        volume = ""
        issue = ""
        pages = ""
        
        if journal_elem is not None:
            journal = journal_elem.findtext(".//Title", "")
            journal_abbrev = journal_elem.findtext(".//ISOAbbreviation", "")
            
            journal_issue = journal_elem.find(".//JournalIssue")
            if journal_issue is not None:
                year = journal_issue.findtext(".//Year", "")
                volume = journal_issue.findtext(".//Volume", "")
                issue = journal_issue.findtext(".//Issue", "")
        
        pages = article.findtext(".//Pagination/MedlinePgn", "")
        
        # Abstract
        abstract_parts = []
        abstract_elem = article.find(".//Abstract")
        if abstract_elem is not None:
            for text_elem in abstract_elem.findall(".//AbstractText"):
                label = text_elem.get("Label", "")
                text = "".join(text_elem.itertext())
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
        
        abstract = " ".join(abstract_parts)
        
        # DOI
        doi = ""
        for id_elem in article.findall(".//ArticleId"):
            if id_elem.get("IdType") == "doi":
                doi = id_elem.text or ""
                break
        
        # MeSH terms
        mesh_terms = []
        for mesh in medline.findall(".//MeshHeading/DescriptorName"):
            mesh_terms.append(mesh.text or "")
        
        return {
            "pmid": pmid,
            "title": title,
            "authors": authors,
            "first_author": authors[0] if authors else "",
            "journal": journal,
            "journal_abbrev": journal_abbrev,
            "year": year,
            "volume": volume,
            "issue": issue,
            "pages": pages,
            "abstract": abstract[:500] + "..." if len(abstract) > 500 else abstract,
            "abstract_full": abstract,
            "doi": doi,
            "mesh_terms": mesh_terms[:5],
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }
    
    def format_vancouver(self, article: Dict[str, Any], index: int = 0) -> str:
        """Format article in Vancouver style (Lancet standard)."""
        authors = article.get("authors", [])
        if len(authors) > 6:
            author_str = ", ".join(authors[:6]) + ", et al."
        else:
            author_str = ", ".join(authors)
        
        parts = [
            f"[{index}]" if index else "",
            author_str,
            article.get("title", ""),
            article.get("journal_abbrev", "") or article.get("journal", ""),
            article.get("year", ""),
        ]
        
        vol_issue = article.get("volume", "")
        if article.get("issue"):
            vol_issue += f"({article['issue']})"
        if vol_issue:
            parts.append(vol_issue)
        
        if article.get("pages"):
            parts.append(article["pages"])
        
        if article.get("doi"):
            parts.append(f"doi: {article['doi']}")
        
        return ". ".join(filter(None, parts)) + "."
    
    def search_for_study(self, exposure: str, outcome: str,
                          max_results: int = 15) -> List[Dict[str, Any]]:
        """Search for literature related to a specific study."""
        queries = [
            f"{exposure} AND {outcome} AND NHANES",
            f"({exposure}) AND ({outcome}) AND National Health and Nutrition Examination Survey",
        ]
        
        all_articles = []
        seen_pmids = set()
        
        for query in queries:
            articles = self.search(query, max_results=max_results // 2 + 2)
            for article in articles:
                if article["pmid"] not in seen_pmids:
                    all_articles.append(article)
                    seen_pmids.add(article["pmid"])
        
        # Sort by year (newest first)
        all_articles.sort(key=lambda x: x.get("year", ""), reverse=True)
        
        return all_articles[:max_results]
    
    def generate_references_section(self, articles: List[Dict[str, Any]]) -> str:
        """Generate a formatted references section."""
        lines = []
        for i, article in enumerate(articles, 1):
            lines.append(self.format_vancouver(article, i))
        return "\n\n".join(lines)
