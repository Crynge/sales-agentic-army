"""
EmailCrafter Agent - Generates personalized outreach emails
"""

from typing import Dict, Any
import structlog
from .base import BaseAgent

logger = structlog.get_logger(__name__)


class EmailCrafterAgent(BaseAgent):
    """Agent that crafts personalized sales emails"""
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email content"""
        self.update_status("executing")
        self.current_task = task
        
        try:
            lead_info = task.get("lead_info", {})
            personalization = task.get("personalization", {})
            campaign_type = task.get("campaign_type", "cold_outreach")
            
            subject = await self._generate_subject(lead_info, campaign_type)
            body = await self._generate_body(lead_info, personalization)
            
            self.tasks_completed += 1
            self.update_status("idle")
            
            return {
                "status": "success",
                "subject": subject,
                "body": body,
                "variants": await self._generate_variants(subject, body),
            }
        except Exception as e:
            logger.exception("Email generation failed")
            self.update_status("error")
            return {
                "status": "error",
                "error": str(e),
            }
        finally:
            self.current_task = None
    
    async def _generate_subject(self, lead_info: Dict, campaign_type: str) -> str:
        """Generate email subject line"""
        company = lead_info.get("company", "there")
        return f"Quick question about {company}'s sales process"
    
    async def _generate_body(self, lead_info: Dict, personalization: Dict) -> str:
        """Generate email body"""
        name = personalization.get("name", "there")
        company = lead_info.get("company", "your company")
        
        return f"""Hi {name},

I noticed that {company} is doing interesting work in your industry. 

We've helped similar companies increase their sales conversion by 30% through our AI-powered automation platform.

Would you be open to a quick 15-minute call next week to explore if there's a fit?

Best regards,
Sales Team"""
    
    async def _generate_variants(self, subject: str, body: str) -> List[Dict[str, str]]:
        """Generate A/B test variants"""
        return [
            {"variant": "A", "subject": subject, "body": body},
            {"variant": "B", "subject": f"Re: {subject}", "body": body.replace("Hi", "Hello")},
        ]
