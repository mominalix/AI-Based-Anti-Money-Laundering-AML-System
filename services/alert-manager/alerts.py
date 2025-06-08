import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import asyncio
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class AlertManager:
    """Manages AML alerts, deduplication, and SAR narrative generation"""
    
    def __init__(self):
        # In-memory storage for demo (in production, use database)
        self.alerts = {}
        
        # Load environment variables from .env file
        # Try to load from root directory first, then current directory
        env_paths = [
            "/app/.env",  # Docker container path
            "../../.env",  # Relative path from service directory
            ".env"  # Current directory
        ]
        
        env_loaded = False
        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path)
                logger.info(f"Loaded environment variables from {env_path}")
                env_loaded = True
                break
        
        if not env_loaded:
            logger.warning("No .env file found, using system environment variables")
        
        # Load configuration from environment
        self.alert_threshold = float(os.getenv("RISK_THRESHOLD_ALERT", "0.7"))
        self.sar_generation_enabled = os.getenv("SAR_GENERATION_ENABLED", "true").lower() == "true"
        self.auto_assign_alerts = os.getenv("AUTO_ASSIGN_ALERTS", "false").lower() == "true"
        
        # Initialize OpenAI client for SAR narrative generation
        self.openai_client = None
        if self.sar_generation_enabled:
            api_key = os.getenv("OPENAI_API_KEY")
            logger.info(f"OpenAI API key status: {'Found' if api_key else 'Not found'}")
            
            if api_key and api_key != "your_openai_api_key_here" and len(api_key.strip()) > 10:
                try:
                    self.openai_client = AsyncOpenAI(api_key=api_key.strip())
                    self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
                    self.openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
                    self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
                    logger.info(f"✅ OpenAI client initialized for SAR generation with model {self.openai_model}")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
                    self.openai_client = None
            else:
                logger.warning("⚠️  OpenAI API key not configured or invalid, using template-based SAR generation")
        
        # Enhanced SAR narrative templates
        self.sar_templates = {
            "high_risk_transaction": """
            SUSPICIOUS ACTIVITY REPORT - HIGH RISK TRANSACTION
            
            Customer ID: {customer_id}
            Transaction ID: {txn_id}
            Amount: ${amount:,.2f} {currency}
            Date: {transaction_date}
            Counterparty Country: {country}
            Risk Score: {risk_score:.2f}
            
            SUSPICIOUS ACTIVITY DESCRIPTION:
            A high-risk transaction has been identified involving customer {customer_id}. The transaction amount of ${amount:,.2f} {currency} to {country} has triggered multiple risk indicators with an overall risk score of {risk_score:.2f}.
            
            RISK FACTORS IDENTIFIED:
            {risk_factors}
            
            RECOMMENDATION:
            This transaction requires immediate investigation and potential filing of a Suspicious Activity Report (SAR) with relevant authorities.
            """,
            
            "suspicious_pattern": """
            SUSPICIOUS ACTIVITY REPORT - PATTERN ANALYSIS
            
            Customer ID: {customer_id}
            Risk Score: {risk_score:.2f}
            Pattern Type: Suspicious Transaction Pattern
            
            SUSPICIOUS ACTIVITY DESCRIPTION:
            Analysis has identified suspicious transaction patterns for customer {customer_id} with a risk score of {risk_score:.2f}. The patterns suggest potential money laundering or other illicit activities.
            
            PATTERN INDICATORS:
            {risk_factors}
            
            RECOMMENDATION:
            Enhanced monitoring and investigation recommended. Consider filing SAR if patterns persist.
            """,
            
            "structuring": """
            SUSPICIOUS ACTIVITY REPORT - STRUCTURING
            
            Customer ID: {customer_id}
            Transaction ID: {txn_id}
            Amount: ${amount:,.2f} {currency}
            Risk Score: {risk_score:.2f}
            
            SUSPICIOUS ACTIVITY DESCRIPTION:
            Potential structuring activity detected for customer {customer_id}. Multiple transactions appear designed to avoid reporting thresholds.
            
            STRUCTURING INDICATORS:
            {risk_factors}
            
            RECOMMENDATION:
            Immediate investigation required. Strong indication of structuring to avoid regulatory reporting requirements.
            """
        }
        
        logger.info(f"AlertManager initialized with threshold {self.alert_threshold}")
    
    async def process_scored_transaction(self, scored_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a scored transaction and potentially create an alert"""
        
        try:
            txn_id = scored_data["txn_id"]
            risk_score = scored_data["risk_score"]
            
            # Only create alerts for high-risk transactions
            if risk_score < self.alert_threshold:
                logger.debug(f"Transaction {txn_id} below alert threshold: {risk_score:.3f}")
                return None
            
            # Check for duplicate alerts (deduplication)
            existing_alert = self._find_existing_alert(txn_id)
            if existing_alert:
                logger.info(f"Alert already exists for transaction {txn_id}")
                return existing_alert
            
            # Determine alert type based on risk score and features
            alert_type = self._determine_alert_type(risk_score, scored_data)
            
            # Create new alert
            alert = await self._create_alert(txn_id, risk_score, alert_type, scored_data)
            
            logger.info(f"Created alert {alert['alert_id']} for transaction {txn_id}")
            return alert
            
        except Exception as e:
            logger.error(f"Error processing scored transaction: {e}")
            return None
    
    async def _create_alert(
        self, 
        txn_id: str, 
        risk_score: float, 
        alert_type: str,
        scored_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new alert"""
        
        alert_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Extract customer ID (simplified - in production, would query transaction data)
        customer_id = f"CUST_{txn_id.split('_')[-1] if '_' in txn_id else txn_id[-1]}"
        
        alert = {
            "alert_id": alert_id,
            "txn_id": txn_id,
            "customer_id": customer_id,
            "risk_score": risk_score,
            "status": "open",
            "alert_type": alert_type,
            "created_at": now,
            "updated_at": now,
            "sar_narrative": None,
            "investigation_notes": None,
            "assigned_to": None
        }
        
        # Generate SAR narrative for very high-risk alerts
        if risk_score >= 0.8:
            try:
                sar_narrative = await self._generate_sar_narrative(alert_type, alert, scored_data)
                # Ensure it's a string, not a coroutine
                if isinstance(sar_narrative, str):
                    alert["sar_narrative"] = sar_narrative
                else:
                    logger.error(f"SAR narrative is not a string: {type(sar_narrative)}")
                    alert["sar_narrative"] = "SAR narrative generation failed - invalid type"
            except Exception as e:
                logger.error(f"Error generating SAR narrative: {e}")
                alert["sar_narrative"] = f"SAR narrative generation failed: {str(e)}"
        
        # Store alert
        self.alerts[alert_id] = alert
        
        return alert
    
    def _determine_alert_type(self, risk_score: float, scored_data: Dict[str, Any]) -> str:
        """Determine the type of alert based on risk factors"""
        
        # Get SHAP values if available
        shap_values = scored_data.get("shap_values", {})
        
        # Determine primary risk factor
        if shap_values.get("pep_exposure", 0) > 0.02:
            return "suspicious_pattern"
        elif shap_values.get("high_risk_country", 0) > 0.02:
            return "high_risk_transaction"
        elif shap_values.get("velocity_score", 0) > 0.02:
            return "velocity_spike"
        elif risk_score >= 0.9:
            return "graph_anomaly"
        else:
            return "high_risk_transaction"
    
    async def _generate_sar_narrative(
        self, 
        alert_type: str, 
        alert: Dict[str, Any],
        scored_data: Dict[str, Any]
    ) -> str:
        """Generate SAR narrative using AI or templates"""
        
        # Try AI-generated narrative first if available
        if self.openai_client:
            try:
                ai_narrative = await self._generate_ai_sar_narrative(alert_type, alert, scored_data)
                if ai_narrative:
                    return ai_narrative
            except Exception as e:
                logger.warning(f"AI SAR generation failed, falling back to templates: {e}")
        
        # Fall back to template-based generation
        return self._generate_template_sar_narrative(alert_type, alert, scored_data)
    
    async def _generate_ai_sar_narrative(
        self,
        alert_type: str,
        alert: Dict[str, Any],
        scored_data: Dict[str, Any]
    ) -> Optional[str]:
        """Generate SAR narrative using OpenAI"""
        
        try:
            # Extract risk factors from SHAP values
            shap_values = scored_data.get("shap_values", {})
            risk_factors = []
            
            for feature, importance in shap_values.items():
                if importance > 0.05:  # Only include significant factors
                    risk_factors.append(f"- {feature}: {importance:.3f}")
            
            risk_factors_text = "\n".join(risk_factors) if risk_factors else "Multiple risk indicators detected"
            
            # Create prompt for SAR generation
            prompt = f"""
            Generate a professional Suspicious Activity Report (SAR) narrative for the following transaction:
            
            Alert Type: {alert_type}
            Customer ID: {alert['customer_id']}
            Transaction ID: {alert['txn_id']}
            Risk Score: {alert['risk_score']:.2f}
            
            Key Risk Factors:
            {risk_factors_text}
            
            Requirements:
            1. Professional, regulatory-compliant language
            2. Clear description of suspicious activity
            3. Specific risk factors identified
            4. Recommendation for next steps
            5. Maximum 400 words
            6. Include all relevant transaction details
            
            Format as a formal SAR narrative suitable for regulatory submission.
            """
            
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert AML compliance officer writing Suspicious Activity Reports for regulatory authorities. Your narratives must be precise, professional, and compliant with banking regulations."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.openai_max_tokens,
                temperature=self.openai_temperature
            )
            
            narrative = response.choices[0].message.content.strip()
            logger.info(f"Generated AI SAR narrative for alert {alert['alert_id']}")
            
            return narrative
            
        except Exception as e:
            logger.error(f"Error generating AI SAR narrative: {e}")
            return None
    
    def _generate_template_sar_narrative(
        self,
        alert_type: str,
        alert: Dict[str, Any],
        scored_data: Dict[str, Any]
    ) -> str:
        """Generate SAR narrative using templates"""
        
        template = self.sar_templates.get(alert_type, self.sar_templates["high_risk_transaction"])
        
        # Extract risk factors from SHAP values
        shap_values = scored_data.get("shap_values", {})
        risk_factors = []
        
        for feature, importance in shap_values.items():
            if importance > 0.05:
                risk_factors.append(f"- {feature.replace('_', ' ').title()}: High impact ({importance:.3f})")
        
        risk_factors_text = "\n".join(risk_factors) if risk_factors else "Multiple risk indicators detected through automated analysis"
        
        # Build context for template
        context = {
            "customer_id": alert["customer_id"],
            "txn_id": alert["txn_id"],
            "amount": 50000,  # Would be extracted from transaction data
            "currency": "USD",  # Would be extracted from transaction data
            "country": "Unknown",  # Would be extracted from transaction data
            "transaction_date": alert["created_at"].strftime("%Y-%m-%d"),
            "risk_score": alert["risk_score"],
            "risk_factors": risk_factors_text
        }
        
        try:
            return template.format(**context).strip()
        except KeyError as e:
            logger.warning(f"Missing template variable {e}, using default narrative")
            return f"""
            SUSPICIOUS ACTIVITY REPORT
            
            Customer ID: {alert['customer_id']}
            Transaction ID: {alert['txn_id']}
            Risk Score: {alert['risk_score']:.2f}
            
            High-risk activity detected through automated analysis. Multiple risk indicators suggest potential money laundering or other illicit activities. Manual investigation required.
            
            Risk Factors:
            {risk_factors_text}
            
            Recommendation: Immediate investigation and potential regulatory filing required.
            """.strip()
    
    def _find_existing_alert(self, txn_id: str) -> Optional[Dict[str, Any]]:
        """Find existing alert for a transaction"""
        for alert in self.alerts.values():
            if alert["txn_id"] == txn_id:
                return alert
        return None
    
    async def get_alerts(
        self,
        status: Optional[str] = None,
        risk_threshold: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get alerts with filtering and pagination"""
        
        # Filter alerts
        filtered_alerts = []
        for alert in self.alerts.values():
            # Status filter
            if status and alert["status"] != status:
                continue
            
            # Risk threshold filter
            if risk_threshold and alert["risk_score"] < risk_threshold:
                continue
            
            filtered_alerts.append(alert)
        
        # Sort by creation date (newest first)
        filtered_alerts.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        
        return filtered_alerts[start_idx:end_idx]
    
    async def count_alerts(
        self,
        status: Optional[str] = None,
        risk_threshold: Optional[float] = None
    ) -> int:
        """Count alerts matching filters"""
        
        count = 0
        for alert in self.alerts.values():
            # Status filter
            if status and alert["status"] != status:
                continue
            
            # Risk threshold filter
            if risk_threshold and alert["risk_score"] < risk_threshold:
                continue
            
            count += 1
        
        return count
    
    async def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get alert by ID"""
        return self.alerts.get(alert_id)
    
    async def update_alert(self, alert_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an alert"""
        
        alert = self.alerts.get(alert_id)
        if not alert:
            return None
        
        # Update fields
        for key, value in updates.items():
            if key in ["status", "investigation_notes", "assigned_to"] and value is not None:
                alert[key] = value
        
        # Update timestamp
        alert["updated_at"] = datetime.utcnow()
        
        logger.info(f"Updated alert {alert_id}")
        return alert
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics for monitoring"""
        
        total_alerts = len(self.alerts)
        if total_alerts == 0:
            return {
                "total_alerts": 0,
                "by_status": {},
                "by_type": {},
                "avg_risk_score": 0.0,
                "high_risk_count": 0
            }
        
        # Count by status
        status_counts = {}
        type_counts = {}
        risk_scores = []
        high_risk_count = 0
        
        for alert in self.alerts.values():
            # Status counts
            status = alert["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Type counts
            alert_type = alert["alert_type"]
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
            
            # Risk score stats
            risk_score = alert["risk_score"]
            risk_scores.append(risk_score)
            
            if risk_score >= 0.8:
                high_risk_count += 1
        
        avg_risk_score = sum(risk_scores) / len(risk_scores)
        
        return {
            "total_alerts": total_alerts,
            "by_status": status_counts,
            "by_type": type_counts,
            "avg_risk_score": avg_risk_score,
            "high_risk_count": high_risk_count
        } 