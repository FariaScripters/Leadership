from typing import Dict, List, Optional, Any, Union
import asyncio
import logging
import json
import re
from datetime import datetime
from .connection import CDPConnection
from .session import CDPSession, TargetInfo
from .page import Page
from .launcher import ChromeLauncher

logger = logging.getLogger(__name__)

class ResearchResult:
    """Represents a research result from paper analysis"""
    def __init__(self, title: str, url: str, abstract: str, date: str):
        self.title = title
        self.url = url
        self.abstract = abstract
        self.date = date
        self.metrics: Dict[str, Any] = {}
        self.key_findings: List[str] = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "title": self.title,
            "url": self.url,
            "abstract": self.abstract,
            "date": self.date,
            "metrics": self.metrics,
            "key_findings": self.key_findings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
class ResearchBrowser:
    """Enhanced browser with research capabilities"""
    
    def __init__(self, connection: CDPConnection):
        self.connection = connection
        self._targets: Dict[str, TargetInfo] = {}
        self._sessions: Dict[str, CDPSession] = {}
        self._pages: Dict[str, Page] = {}
        self.current_task: Optional[str] = None
        
    @classmethod
    async def launch(cls, headless: bool = True) -> "ResearchBrowser":
        """Launch new browser instance"""
        launcher = ChromeLauncher()
        connection = await launcher.launch(headless=headless)
        browser = cls(connection)
        await browser._setup_target_discovery()
        return browser
        
    async def _setup_target_discovery(self):
        """Setup target discovery and tracking"""
        async def on_target_created(params: Dict[str, Any]):
            target_info = params["targetInfo"]
            target = TargetInfo(
                target_id=target_info["targetId"],
                type=target_info["type"],
                title=target_info["title"],
                url=target_info["url"],
                attached=target_info["attached"],
                browser_context_id=target_info.get("browserContextId")
            )
            self._targets[target.target_id] = target
            if target.type == "page" and not target.attached:
                await self.attach_to_target(target.target_id)
                
        self.connection.on("Target.targetCreated", on_target_created)
        await self.connection.send_command(
            "Target.setDiscoverTargets",
            {"discover": True}
        )
        
    async def attach_to_target(self, target_id: str) -> Optional[Page]:
        """Attach to target and create session"""
        target = self._targets.get(target_id)
        if not target:
            return None
            
        response = await self.connection.send_command(
            "Target.attachToTarget",
            {
                "targetId": target_id,
                "flatten": True
            }
        )
        session_id = response["sessionId"]
        
        session = CDPSession(self.connection, target, session_id)
        self._sessions[target_id] = session
        
        if target.type == "page":
            page = Page(session)
            self._pages[target_id] = page
            return page
            
        return None
        
    async def new_page(self) -> Page:
        """Create new page"""
        response = await self.connection.send_command(
            "Target.createTarget",
            {"url": "about:blank"}
        )
        target_id = response["targetId"]
        
        while target_id not in self._pages:
            await asyncio.sleep(0.1)
            
        return self._pages[target_id]
        
    async def search_papers(
        self,
        query: str,
        source: str = "arxiv"
    ) -> List[ResearchResult]:
        """Search for research papers
        
        Args:
            query: Search query
            source: Paper source ("arxiv", "paperswithcode", etc)
            
        Returns:
            List of research results
        """
        page = await self.new_page()
        results = []
        
        if source == "arxiv":
            # Navigate to arXiv search
            await page.navigate(
                f"https://arxiv.org/search/?query={query}&searchtype=all"
            )
            
            # Extract paper details
            papers = await page.evaluate("""
                Array.from(document.querySelectorAll('.arxiv-result')).map(paper => ({
                    title: paper.querySelector('p.title').textContent,
                    abstract: paper.querySelector('p.abstract').textContent,
                    url: paper.querySelector('p.list-title a:last-child').href,
                    date: paper.querySelector('p.is-size-7').textContent
                }))
            """)
            
            for paper in papers:
                result = ResearchResult(
                    title=paper["title"].strip(),
                    abstract=paper["abstract"].strip(),
                    url=paper["url"],
                    date=paper["date"].strip()
                )
                results.append(result)
                
        await page.close()
        return results
        
    async def analyze_paper(self, url: str) -> ResearchResult:
        """Analyze a research paper
        
        Args:
            url: Paper URL
            
        Returns:
            Research result with analysis
        """
        page = await self.new_page()
        
        # Navigate to paper
        await page.navigate(url)
        
        # Extract paper details
        data = await page.evaluate("""
            () => {
                const title = document.querySelector('h1')?.textContent || '';
                const abstract = document.querySelector('.abstract')?.textContent || '';
                const date = document.querySelector('.dateline')?.textContent || '';
                return {title, abstract, date, url: window.location.href};
            }
        """)
        
        result = ResearchResult(
            title=data["title"].strip(),
            abstract=data["abstract"].strip(),
            url=data["url"],
            date=data["date"].strip()
        )
        
        # Extract metrics and findings
        # This would integrate with your LLM service to analyze the paper
        
        await page.close()
        return result
        
    async def close(self):
        """Close browser and cleanup"""
        for page in self._pages.values():
            await page.close()
        for session in self._sessions.values():
            await session.detach()
        await self.connection.disconnect()
