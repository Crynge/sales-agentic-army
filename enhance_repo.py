#!/usr/bin/env python3
"""
Repository Enhancement Script
Adds enterprise-grade components to sales-agentic-army repo
"""

import os
import json
from pathlib import Path

BASE_DIR = Path("/workspace/sales-agentic-army")

def create_file(path: str, content: str):
    """Create a file with content"""
    full_path = BASE_DIR / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, 'w') as f:
        f.write(content)
    print(f"✅ Created: {path}")

# Create EmailCrafter agent
create_file("src/agents/email_crafter.py", '''"""
EmailCrafter Agent - AI-powered personalized email generation
Creates high-converting outreach emails with A/B testing capabilities
"""

from typing import Dict, Any, List, Optional
from pydantic import Field
import structlog
from datetime import datetime

from .base import BaseAgent, AgentConfig, TaskResult

logger = structlog.get_logger(__name__)


class EmailCrafterConfig(AgentConfig):
    """Configuration for EmailCrafter agent"""
    llm_model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 500
    tone: str = "professional"  # professional, casual, enthusiastic
    personalization_depth: str = "high"  # low, medium, high
    ab_testing_enabled: bool = True
    compliance_check: bool = True


class EmailCrafter(BaseAgent):
    """
    Autonomous email crafting agent with personalization and A/B testing.
    
    Capabilities:
    - Multi-variant email generation
    - Personalization at scale
    - Tone optimization
    - CAN-SPAM/GDPR compliance checking
    - A/B test variant creation
    - Performance tracking integration
    """
    
    def __init__(self, config: EmailCrafterConfig):
        super().__init__(config)
        self.config: EmailCrafterConfig = config
    
    def get_capabilities(self) -> List[str]:
        return [
            "email_generation",
            "personalization",
            "ab_testing",
            "compliance_check",
            "tone_optimization",
            "subject_line_optimization",
            "cta_optimization",
        ]
    
    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """Execute email crafting task"""
        task_type = task.get("type")
        
        if task_type == "generate_email":
            return await self._generate_email(task.get("payload", {}))
        elif task_type == "generate_variants":
            return await self._generate_variants(task.get("payload", {}))
        elif task_type == "optimize_subject":
            return await self._optimize_subject(task.get("payload", {}))
        elif task_type == "check_compliance":
            return await self._check_compliance(task.get("payload", {}))
        else:
            return TaskResult(
                success=False,
                error=f"Unknown task type: {task_type}",
            )
    
    async def _generate_email(self, payload: Dict[str, Any]) -> TaskResult:
        """Generate personalized email"""
        try:
            prospect = payload.get("prospect", {})
            sender = payload.get("sender", {})
            campaign_goal = payload.get("campaign_goal", "demo_request")
            
            # Extract key information
            prospect_name = prospect.get("name", "there")
            company = prospect.get("company", {}).get("name", "")
            industry = prospect.get("company", {}).get("industry", "")
            pain_points = prospect.get("pain_points", [])
            
            # Generate email components
            subject = self._generate_subject_line(prospect, campaign_goal)
            body = self._generate_body(prospect, sender, campaign_goal)
            cta = self._generate_cta(campaign_goal)
            
            email_content = f"""Subject: {subject}

Hi {prospect_name},

{body}

{cta}

Best regards,
{sender.get('name', '')}
{sender.get('title', '')}
{sender.get('company', '')}
"""
            
            logger.info("Email generated", prospect=prospect_name, company=company)
            
            return TaskResult(
                success=True,
                data={
                    "email": email_content,
                    "subject": subject,
                    "body": body,
                    "cta": cta,
                    "personalization_score": self._calculate_personalization_score(prospect),
                    "estimated_open_rate": self._predict_open_rate(subject),
                },
                metadata={"model": self.config.llm_model, "tone": self.config.tone},
            )
            
        except Exception as e:
            logger.exception("Email generation failed", error=str(e))
            return TaskResult(success=False, error=str(e))
    
    async def _generate_variants(self, payload: Dict[str, Any]) -> TaskResult:
        """Generate A/B test variants"""
        try:
            base_payload = payload.get("base_email", {})
            num_variants = payload.get("num_variants", 3)
            
            variants = []
            for i in range(num_variants):
                variant = await self._generate_email(base_payload)
                if variant.success:
                    variants.append({
                        "variant_id": f"A{i+1}",
                        "content": variant.data["email"],
                        "hypothesis": f"Variant {i+1} will improve conversion by testing different approach",
                    })
            
            return TaskResult(
                success=True,
                data={
                    "variants": variants,
                    "test_recommendation": "Start with 20% traffic split, monitor for 48 hours",
                },
                metadata={"num_variants": len(variants)},
            )
            
        except Exception as e:
            logger.exception("Variant generation failed", error=str(e))
            return TaskResult(success=False, error=str(e))
    
    async def _optimize_subject(self, payload: Dict[str, Any]) -> TaskResult:
        """Optimize subject line for open rate"""
        try:
            subject = payload.get("subject", "")
            
            optimizations = {
                "original": subject,
                "shorter": subject[:40] + "..." if len(subject) > 40 else subject,
                "question": self._convert_to_question(subject),
                "personalized": self._add_personalization(subject),
                "urgency": self._add_urgency(subject),
                "curiosity": self._add_curiosity(subject),
            }
            
            scores = {k: self._predict_open_rate(v) for k, v in optimizations.items()}
            best = max(scores, key=scores.get)
            
            return TaskResult(
                success=True,
                data={
                    "optimizations": optimizations,
                    "predicted_scores": scores,
                    "recommendation": best,
                    "best_score": scores[best],
                },
                metadata={"optimization_model": "open_rate_predictor_v2"},
            )
            
        except Exception as e:
            logger.exception("Subject optimization failed", error=str(e))
            return TaskResult(success=False, error=str(e))
    
    async def _check_compliance(self, payload: Dict[str, Any]) -> TaskResult:
        """Check email for CAN-SPAM and GDPR compliance"""
        try:
            email_content = payload.get("email", "")
            
            issues = []
            recommendations = []
            
            # CAN-SPAM checks
            if "unsubscribe" not in email_content.lower():
                issues.append("Missing unsubscribe mechanism")
                recommendations.append("Add clear unsubscribe link")
            
            if "@" not in email_content:
                issues.append("Missing sender email address")
                recommendations.append("Include physical mailing address")
            
            # GDPR checks
            if "privacy" not in email_content.lower() and "data" not in email_content.lower():
                recommendations.append("Consider adding privacy policy link for GDPR")
            
            is_compliant = len(issues) == 0
            
            return TaskResult(
                success=True,
                data={
                    "is_compliant": is_compliant,
                    "issues": issues,
                    "recommendations": recommendations,
                    "regulations_checked": ["CAN-SPAM", "GDPR"],
                },
                metadata={"check_timestamp": datetime.utcnow().isoformat()},
            )
            
        except Exception as e:
            logger.exception("Compliance check failed", error=str(e))
            return TaskResult(success=False, error=str(e))
    
    def _generate_subject_line(self, prospect: Dict, goal: str) -> str:
        """Generate compelling subject line"""
        company = prospect.get("company", {}).get("name", "")
        name = prospect.get("name", "")
        
        templates = {
            "demo_request": [
                f"Quick question about {company}'s sales process",
                f"Idea for {company}, {name}",
                f"{company} + [Your Company] = ?",
            ],
            "partnership": [
                f"Partnership opportunity for {company}",
                f"Thought you'd find this interesting, {name}",
            ],
            "follow_up": [
                f"Re: Our conversation",
                f"Following up on my previous email",
            ],
        }
        
        options = templates.get(goal, templates["demo_request"])
        return options[0] if options else f"Quick question about {company}"
    
    def _generate_body(self, prospect: Dict, sender: Dict, goal: str) -> str:
        """Generate personalized email body"""
        name = prospect.get("name", "")
        company = prospect.get("company", {}).get("name", "")
        
        # Personalized opening
        openings = [
            f"I've been following {company}'s growth in the market,",
            f"I noticed {company} has been making waves recently,",
            f"Congratulations on {company}'s recent achievements,",
        ]
        
        # Value proposition
        value_props = [
            "We help companies like yours increase sales productivity by 40%.",
            "Our platform has helped similar teams close 2x more deals.",
            "Companies in your space are seeing 3x ROI within 90 days.",
        ]
        
        # Social proof
        social_proof = [
            "Teams at Fortune 500 companies trust us.",
            "Used by over 10,000 sales professionals.",
            "Rated 4.9/5 on G2.",
        ]
        
        body = f"{openings[0]}\\n\\n{value_props[0]}\\n\\n{socal_proof[0]}"
        return body
    
    def _generate_cta(self, goal: str) -> str:
        """Generate call-to-action"""
        ctas = {
            "demo_request": "Would you be open to a 15-minute demo next week?",
            "partnership": "Are you available for a quick chat this Thursday?",
            "follow_up": "Let me know if you'd like to explore this further.",
        }
        return ctas.get(goal, "Would love to hear your thoughts.")
    
    def _calculate_personalization_score(self, prospect: Dict) -> float:
        """Calculate personalization score 0-100"""
        score = 0
        if prospect.get("name"): score += 20
        if prospect.get("company", {}).get("name"): score += 20
        if prospect.get("company", {}).get("industry"): score += 15
        if prospect.get("pain_points"): score += 25
        if prospect.get("recent_news"): score += 20
        return min(score, 100)
    
    def _predict_open_rate(self, subject: str) -> float:
        """Predict open rate percentage"""
        score = 15.0  # baseline
        
        # Length bonus (30-50 chars is optimal)
        if 30 <= len(subject) <= 50:
            score += 10
        
        # Personalization bonus
        if any(word in subject.lower() for word in ["you", "your", company]):
            score += 15
        
        # Question bonus
        if "?" in subject:
            score += 8
        
        # Urgency bonus (but not too much)
        if any(word in subject.lower() for word in ["quick", "today", "now"]):
            score += 5
        
        return min(score, 45.0)  # Cap at 45%
    
    def _convert_to_question(self, text: str) -> str:
        """Convert statement to question"""
        if text.endswith("?"):
            return text
        return f"Quick question: {text.rstrip('.')}"
    
    def _add_personalization(self, text: str) -> str:
        """Add personalization placeholder"""
        return f"[Name], {text}"
    
    def _add_urgency(self, text: str) -> str:
        """Add urgency indicator"""
        return f"Today only: {text}"
    
    def _add_curiosity(self, text: str) -> str:
        """Add curiosity element"""
        return f"You won't believe this... {text}"
''')

print("\n🎉 Repository enhancement complete!")
print("Files created successfully.")
