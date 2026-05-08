"""
LeadFinder Agent - Advanced prospecting and lead enrichment
Discovers, qualifies, and enriches B2B leads using multiple data sources
"""

from typing import Dict, Any, List, Optional
from pydantic import Field
import structlog
import httpx
from datetime import datetime

from .base import BaseAgent, AgentConfig, TaskResult, AgentStatus

logger = structlog.get_logger(__name__)


class LeadFinderConfig(AgentConfig):
    """Configuration for LeadFinder agent"""
    clearbit_api_key: Optional[str] = None
    linkedin_proxy_url: Optional[str] = None
    crunchbase_api_key: Optional[str] = None
    max_leads_per_search: int = 100
    enrichment_depth: str = "standard"  # basic, standard, deep
    filters: Dict[str, Any] = Field(default_factory=dict)


class LeadFinder(BaseAgent):
    """
    Autonomous lead discovery and enrichment agent.
    
    Capabilities:
    - Multi-source lead discovery (LinkedIn, Clearbit, Crunchbase)
    - Company and contact enrichment
    - Lead scoring based on ICP fit
    - Duplicate detection
    - Intent signal detection
    """
    
    def __init__(self, config: LeadFinderConfig):
        super().__init__(config)
        self.config: LeadFinderConfig = config
        self._http_client: Optional[httpx.AsyncClient] = None
    
    def get_capabilities(self) -> List[str]:
        return [
            "lead_discovery",
            "company_enrichment",
            "contact_enrichment",
            "lead_scoring",
            "duplicate_detection",
            "intent_signal_detection",
            "icp_matching",
        ]
    
    async def initialize(self) -> None:
        """Initialize HTTP client and connections"""
        await super().initialize()
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            headers={
                "User-Agent": "SalesAgenticArmy/1.0",
                "Accept": "application/json",
            },
        )
        logger.info("LeadFinder initialized", agent_id=self.agent_id)
    
    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """Execute lead finding task"""
        task_type = task.get("type")
        
        if task_type == "discover_leads":
            return await self._discover_leads(task.get("payload", {}))
        elif task_type == "enrich_lead":
            return await self._enrich_lead(task.get("payload", {}))
        elif task_type == "score_lead":
            return await self._score_lead(task.get("payload", {}))
        elif task_type == "find_similar":
            return await self._find_similar_leads(task.get("payload", {}))
        else:
            return TaskResult(
                success=False,
                error=f"Unknown task type: {task_type}",
                metadata={"supported_types": ["discover_leads", "enrich_lead", "score_lead", "find_similar"]},
            )
    
    async def _discover_leads(self, payload: Dict[str, Any]) -> TaskResult:
        """Discover new leads based on criteria"""
        try:
            criteria = payload.get("criteria", {})
            industry = criteria.get("industry")
            company_size = criteria.get("company_size")
            location = criteria.get("location")
            technologies = criteria.get("technologies", [])
            
            leads = []
            
            # Search Clearbit if configured
            if self.config.clearbit_api_key:
                clearbit_leads = await self._search_clearbit(criteria)
                leads.extend(clearbit_leads)
            
            # Search Crunchbase if configured
            if self.config.crunchbase_api_key:
                crunchbase_leads = await self._search_crunchbase(criteria)
                leads.extend(crunchbase_leads)
            
            # Remove duplicates
            unique_leads = self._deduplicate_leads(leads)
            
            # Apply ICP filters
            filtered_leads = self._apply_icp_filters(unique_leads, criteria)
            
            logger.info(
                "Lead discovery completed",
                found=len(filtered_leads),
                criteria=criteria,
            )
            
            return TaskResult(
                success=True,
                data={
                    "leads": filtered_leads[:self.config.max_leads_per_search],
                    "total_found": len(filtered_leads),
                    "sources_used": ["clearbit", "crunchbase"] if self.config.clearbit_api_key else ["crunchbase"],
                },
                metadata={"search_criteria": criteria},
            )
            
        except Exception as e:
            logger.exception("Lead discovery failed", error=str(e))
            return TaskResult(success=False, error=str(e))
    
    async def _enrich_lead(self, payload: Dict[str, Any]) -> TaskResult:
        """Enrich existing lead with additional data"""
        try:
            lead_id = payload.get("lead_id")
            domain = payload.get("domain")
            email = payload.get("email")
            
            if not domain and not email:
                return TaskResult(success=False, error="Domain or email required")
            
            enriched_data = {}
            
            # Enrich from Clearbit
            if self.config.clearbit_api_key and domain:
                clearbit_data = await self._enrich_from_clearbit(domain)
                enriched_data["clearbit"] = clearbit_data
            
            # Enrich from Crunchbase
            if self.config.crunchbase_api_key and domain:
                crunchbase_data = await self._enrich_from_crunchbase(domain)
                enriched_data["crunchbase"] = crunchbase_data
            
            # Add intent signals
            intent_signals = await self._detect_intent_signals(domain)
            enriched_data["intent_signals"] = intent_signals
            
            logger.info("Lead enriched", lead_id=lead_id, domain=domain)
            
            return TaskResult(
                success=True,
                data={
                    "lead_id": lead_id,
                    "domain": domain,
                    "enriched_data": enriched_data,
                    "enrichment_timestamp": datetime.utcnow().isoformat(),
                },
                metadata={"enrichment_depth": self.config.enrichment_depth},
            )
            
        except Exception as e:
            logger.exception("Lead enrichment failed", error=str(e))
            return TaskResult(success=False, error=str(e))
    
    async def _score_lead(self, payload: Dict[str, Any]) -> TaskResult:
        """Score lead based on ICP fit and engagement signals"""
        try:
            lead = payload.get("lead", {})
            
            score = 0
            max_score = 100
            scoring_factors = {}
            
            # Company size score (0-25)
            employee_count = lead.get("company", {}).get("employee_count", 0)
            if 50 <= employee_count <= 5000:
                size_score = 25
            elif 10 <= employee_count < 50 or 5000 < employee_count <= 10000:
                size_score = 15
            else:
                size_score = 5
            scoring_factors["company_size"] = size_score
            score += size_score
            
            # Industry match score (0-25)
            target_industries = self.config.filters.get("target_industries", [])
            lead_industry = lead.get("company", {}).get("industry", "")
            if target_industries and lead_industry in target_industries:
                industry_score = 25
            else:
                industry_score = 10
            scoring_factors["industry_match"] = industry_score
            score += industry_score
            
            # Technology stack score (0-25)
            required_techs = self.config.filters.get("required_technologies", [])
            lead_techs = lead.get("company", {}).get("technologies", [])
            if required_techs:
                tech_matches = len(set(required_techs) & set(lead_techs))
                tech_score = min(25, tech_matches * 8)
            else:
                tech_score = 15
            scoring_factors["technology_fit"] = tech_score
            score += tech_score
            
            # Intent signals score (0-25)
            intent_signals = lead.get("intent_signals", [])
            intent_score = min(25, len(intent_signals) * 5)
            scoring_factors["intent_signals"] = intent_score
            score += intent_score
            
            # Determine lead tier
            if score >= 80:
                tier = "A - Hot Lead"
            elif score >= 60:
                tier = "B - Warm Lead"
            elif score >= 40:
                tier = "C - Cold Lead"
            else:
                tier = "D - Unqualified"
            
            logger.info("Lead scored", score=score, tier=tier)
            
            return TaskResult(
                success=True,
                data={
                    "score": score,
                    "max_score": max_score,
                    "tier": tier,
                    "scoring_factors": scoring_factors,
                    "recommendation": self._get_recommendation(score, tier),
                },
                metadata={"scoring_model": "icp_fit_v1"},
            )
            
        except Exception as e:
            logger.exception("Lead scoring failed", error=str(e))
            return TaskResult(success=False, error=str(e))
    
    async def _find_similar_leads(self, payload: Dict[str, Any]) -> TaskResult:
        """Find leads similar to a given seed lead"""
        try:
            seed_lead = payload.get("seed_lead", {})
            similarity_threshold = payload.get("threshold", 0.7)
            
            # Extract key attributes from seed
            seed_industry = seed_lead.get("company", {}).get("industry")
            seed_size = seed_lead.get("company", {}).get("employee_count")
            seed_techs = seed_lead.get("company", {}).get("technologies", [])
            
            # Find similar (simplified - would use vector similarity in production)
            similar_leads = await self._discover_leads({
                "criteria": {
                    "industry": seed_industry,
                    "company_size": {"min": seed_size * 0.5, "max": seed_size * 2},
                    "technologies": seed_techs[:3],
                }
            })
            
            return TaskResult(
                success=True,
                data={
                    "seed_lead": seed_lead,
                    "similar_leads": similar_leads.data.get("leads", []) if similar_leads.success else [],
                    "similarity_threshold": similarity_threshold,
                },
                metadata={"search_method": "attribute_matching"},
            )
            
        except Exception as e:
            logger.exception("Similar lead search failed", error=str(e))
            return TaskResult(success=False, error=str(e))
    
    async def _search_clearbit(self, criteria: Dict[str, Any]) -> List[Dict]:
        """Search Clearbit API for leads"""
        if not self._http_client:
            return []
        
        try:
            response = await self._http_client.get(
                "https://person.clearbit.com/v2/combined/find",
                params={"company": criteria.get("industry", "")},
                headers={"Authorization": f"Bearer {self.config.clearbit_api_key}"},
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception as e:
            logger.warning("Clearbit search failed", error=str(e))
            return []
    
    async def _search_crunchbase(self, criteria: Dict[str, Any]) -> List[Dict]:
        """Search Crunchbase API for leads"""
        if not self._http_client:
            return []
        
        try:
            response = await self._http_client.get(
                "https://api.crunchbase.com/api/v4/searches/organizations",
                json={"query": criteria},
                headers={"Authorization": f"Bearer {self.config.crunchbase_api_key}"},
            )
            response.raise_for_status()
            return response.json().get("entities", [])
        except Exception as e:
            logger.warning("Crunchbase search failed", error=str(e))
            return []
    
    async def _enrich_from_clearbit(self, domain: str) -> Dict:
        """Enrich company data from Clearbit"""
        if not self._http_client or not self.config.clearbit_api_key:
            return {}
        
        try:
            response = await self._http_client.get(
                f"https://company.clearbit.com/v2/companies/find?domain={domain}",
                headers={"Authorization": f"Bearer {self.config.clearbit_api_key}"},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("Clearbit enrichment failed", error=str(e))
            return {}
    
    async def _enrich_from_crunchbase(self, domain: str) -> Dict:
        """Enrich company data from Crunchbase"""
        if not self._http_client or not self.config.crunchbase_api_key:
            return {}
        
        try:
            response = await self._http_client.get(
                f"https://api.crunchbase.com/api/v4/entities/organizations/{domain}",
                headers={"Authorization": f"Bearer {self.config.crunchbase_api_key}"},
            )
            response.raise_for_status()
            return response.json().get("properties", {})
        except Exception as e:
            logger.warning("Crunchbase enrichment failed", error=str(e))
            return {}
    
    async def _detect_intent_signals(self, domain: str) -> List[Dict]:
        """Detect buying intent signals for a company"""
        # Placeholder - would integrate with Bombora, G2, etc.
        return []
    
    def _deduplicate_leads(self, leads: List[Dict]) -> List[Dict]:
        """Remove duplicate leads based on domain"""
        seen_domains = set()
        unique = []
        
        for lead in leads:
            domain = lead.get("company", {}).get("domain", "")
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                unique.append(lead)
        
        return unique
    
    def _apply_icp_filters(self, leads: List[Dict], criteria: Dict[str, Any]) -> List[Dict]:
        """Filter leads based on Ideal Customer Profile"""
        filtered = []
        
        for lead in leads:
            company = lead.get("company", {})
            
            # Check employee count
            min_size = criteria.get("min_employees", 0)
            max_size = criteria.get("max_employees", float("inf"))
            emp_count = company.get("employee_count", 0)
            if not (min_size <= emp_count <= max_size):
                continue
            
            # Check industry
            target_industries = criteria.get("industries", [])
            if target_industries:
                lead_industry = company.get("industry", "")
                if lead_industry not in target_industries:
                    continue
            
            filtered.append(lead)
        
        return filtered
    
    def _get_recommendation(self, score: int, tier: str) -> str:
        """Get action recommendation based on score"""
        if tier == "A - Hot Lead":
            return "Immediate outreach recommended. Assign to senior SDR."
        elif tier == "B - Warm Lead":
            return "Add to nurture campaign. Follow up within 48 hours."
        elif tier == "C - Cold Lead":
            return "Add to long-term nurture. Re-evaluate in 30 days."
        else:
            return "Not a good fit. Archive or disqualify."
    
    async def shutdown(self) -> None:
        """Cleanup resources"""
        if self._http_client:
            await self._http_client.aclose()
        await super().shutdown()
