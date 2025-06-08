import math
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class FeatureEngine:
    """Feature engineering for AML risk assessment"""
    
    def __init__(self):
        # Load configuration from environment
        self.velocity_window_days = int(os.getenv("VELOCITY_WINDOW_DAYS", "30"))
        self.velocity_short_window_days = int(os.getenv("VELOCITY_SHORT_WINDOW_DAYS", "7"))
        self.country_risk_high_threshold = float(os.getenv("COUNTRY_RISK_HIGH_THRESHOLD", "0.6"))
        
        # Load country risk scores from external data source
        self.country_risk_scores = self._load_country_risk_data()
        
        # Load KYC level mappings
        self.kyc_scores = {
            "basic": 0.7,
            "standard": 0.3,
            "enhanced": 0.1
        }
        
        # Load sanctions and PEP data
        self.sanctions_countries = self._load_sanctions_data()
        self.high_risk_countries = self._load_high_risk_countries()
        
        logger.info(f"FeatureEngine initialized with {len(self.country_risk_scores)} countries")
    
    def _load_country_risk_data(self) -> Dict[str, float]:
        """Load country risk scores from data source"""
        # In production, this would load from external API or database
        # For now, using comprehensive country risk mapping
        return {
            # Low risk countries (0.0 - 0.2)
            "US": 0.1, "GB": 0.1, "DE": 0.1, "FR": 0.1, "CA": 0.1, "AU": 0.1, "JP": 0.1,
            "NL": 0.1, "SE": 0.1, "NO": 0.1, "DK": 0.1, "FI": 0.1, "SG": 0.15, "HK": 0.15,
            
            # Medium-low risk (0.2 - 0.4)
            "SA": 0.3, "AE": 0.25, "QA": 0.25, "KW": 0.3, "BH": 0.25, "OM": 0.3,
            "BR": 0.35, "MX": 0.3, "AR": 0.35, "CL": 0.25, "CO": 0.4, "PE": 0.35,
            "IN": 0.3, "TH": 0.3, "MY": 0.25, "ID": 0.35, "PH": 0.4, "VN": 0.35,
            
            # Medium-high risk (0.4 - 0.6)
            "CN": 0.45, "RU": 0.55, "TR": 0.45, "EG": 0.5, "ZA": 0.4, "NG": 0.55,
            "KE": 0.45, "GH": 0.5, "UG": 0.5, "TZ": 0.45, "BD": 0.5, "PK": 0.55,
            
            # High risk (0.6 - 0.8)
            "CH": 0.6, "LU": 0.6, "MC": 0.65, "LI": 0.6, "AD": 0.6,  # Tax havens
            "KY": 0.75, "BM": 0.7, "BS": 0.7, "BZ": 0.7, "PA": 0.65, "CR": 0.6,
            "VG": 0.75, "AI": 0.7, "TC": 0.7, "GG": 0.65, "JE": 0.65, "IM": 0.65,
            
            # Very high risk (0.8 - 1.0)
            "AF": 0.95, "IR": 0.9, "KP": 0.95, "SY": 0.9, "IQ": 0.85, "YE": 0.85,
            "SO": 0.9, "LY": 0.85, "SD": 0.85, "MM": 0.8, "BY": 0.8, "VE": 0.8,
            "CU": 0.8, "ZW": 0.85, "ER": 0.85, "CF": 0.85, "TD": 0.8, "ML": 0.8
        }
    
    def _load_sanctions_data(self) -> List[str]:
        """Load sanctioned countries list"""
        return ["AF", "IR", "KP", "SY", "IQ", "YE", "SO", "LY", "SD", "MM", "BY", "VE", "CU"]
    
    def _load_high_risk_countries(self) -> List[str]:
        """Load high-risk countries for enhanced monitoring"""
        return ["KY", "BM", "BS", "BZ", "PA", "CR", "VG", "AI", "TC", "GG", "JE", "IM", "CH", "LU", "MC", "LI", "AD"]
    
    def parse_timestamp(self, ts_str: str) -> datetime:
        """Parse timestamp handling various formats and timezone issues"""
        # Handle various timestamp formats
        if '+00:00+00:00' in ts_str:
            ts_str = ts_str.replace('+00:00+00:00', '+00:00')
        elif ts_str.endswith('Z'):
            ts_str = ts_str.replace('Z', '+00:00')
        # Remove any remaining duplicate timezone info
        if ts_str.count('+00:00') > 1:
            ts_str = ts_str.replace('+00:00', '', ts_str.count('+00:00') - 1)
        return datetime.fromisoformat(ts_str)
    
    async def compute_features(
        self, 
        transaction: Dict[str, Any],
        transaction_store: Dict[str, Any],
        customer_store: Dict[str, Any],
        account_store: Dict[str, Any]
    ) -> Dict[str, float]:
        """Compute all features for a transaction"""
        
        features = {}
        
        try:
            # Basic transaction features
            features.update(self._compute_transaction_features(transaction))
            
            # Velocity features
            features.update(self._compute_velocity_features(
                transaction, transaction_store
            ))
            
            # Country risk features
            features.update(self._compute_country_risk_features(transaction))
            
            # Customer/KYC features
            features.update(self._compute_customer_features(
                transaction, customer_store, account_store
            ))
            
            # Time-based features
            features.update(self._compute_time_features(transaction))
            
            logger.info(f"Computed {len(features)} features for transaction {transaction['txn_id']}")
            
        except Exception as e:
            logger.error(f"Error computing features: {e}")
            # Return default features on error
            features = self._get_default_features()
        
        return features
    
    def _compute_transaction_features(self, transaction: Dict[str, Any]) -> Dict[str, float]:
        """Compute basic transaction-level features"""
        amount = float(transaction["amount"])
        
        return {
            "amount": amount,
            "amount_log": math.log(max(amount, 1)),
            "amount_rounded": 1.0 if amount % 1000 == 0 else 0.0,  # Round number indicator
            "amount_threshold_10k": 1.0 if amount >= 10000 else 0.0,
            "amount_threshold_50k": 1.0 if amount >= 50000 else 0.0,
        }
    
    def _compute_velocity_features(
        self, 
        transaction: Dict[str, Any], 
        transaction_store: Dict[str, Any]
    ) -> Dict[str, float]:
        """Compute velocity-based features with enhanced analytics"""
        
        account_id = transaction["account_id"]
        
        # Handle different timestamp formats
        timestamp_str = transaction["timestamp"]
        if '+00:00+00:00' in timestamp_str:
            timestamp_str = timestamp_str.replace('+00:00+00:00', '+00:00')
        elif timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str.replace('Z', '+00:00')
        # Remove any remaining duplicate timezone info
        if timestamp_str.count('+00:00') > 1:
            timestamp_str = timestamp_str.replace('+00:00', '', timestamp_str.count('+00:00') - 1)
        
        txn_timestamp = datetime.fromisoformat(timestamp_str)
        current_amount = float(transaction["amount"])
        
        # Get transactions for the same account
        account_txns = [
            txn for txn in transaction_store.values()
            if txn["account_id"] == account_id and txn["txn_id"] != transaction["txn_id"]
        ]
        
        # Sort transactions by timestamp
        account_txns.sort(key=lambda x: self.parse_timestamp(x["timestamp"]))
        
        # Long-term velocity (configurable window)
        long_window_ago = txn_timestamp - timedelta(days=self.velocity_window_days)
        long_term_txns = [
            txn for txn in account_txns
            if self.parse_timestamp(txn["timestamp"]) >= long_window_ago
        ]
        
        # Short-term velocity (configurable window)
        short_window_ago = txn_timestamp - timedelta(days=self.velocity_short_window_days)
        short_term_txns = [
            txn for txn in account_txns
            if self.parse_timestamp(txn["timestamp"]) >= short_window_ago
        ]
        
        # Calculate amounts and counts
        amt_long = sum(float(txn["amount"]) for txn in long_term_txns)
        count_long = len(long_term_txns)
        amt_short = sum(float(txn["amount"]) for txn in short_term_txns)
        count_short = len(short_term_txns)
        
        # Calculate averages
        avg_amt_long = amt_long / max(count_long, 1)
        avg_amt_short = amt_short / max(count_short, 1)
        
        # Velocity scores
        daily_velocity_long = count_long / max(self.velocity_window_days, 1)
        daily_velocity_short = count_short / max(self.velocity_short_window_days, 1)
        
        # Acceleration (change in velocity)
        velocity_acceleration = max(0, daily_velocity_short - daily_velocity_long)
        
        # Amount deviation from historical average
        amount_deviation = abs(current_amount - avg_amt_long) / max(avg_amt_long, 1) if avg_amt_long > 0 else 0
        
        # Structuring detection (amounts just below reporting thresholds)
        structuring_indicators = self._detect_structuring_patterns(current_amount, account_txns, txn_timestamp)
        
        return {
            f"amt_{self.velocity_window_days}d": amt_long,
            f"count_{self.velocity_window_days}d": float(count_long),
            f"avg_amt_{self.velocity_window_days}d": avg_amt_long,
            f"amt_{self.velocity_short_window_days}d": amt_short,
            f"count_{self.velocity_short_window_days}d": float(count_short),
            f"avg_amt_{self.velocity_short_window_days}d": avg_amt_short,
            "velocity_score": min(daily_velocity_long, 1.0),
            "velocity_acceleration": min(velocity_acceleration, 1.0),
            "amount_deviation": min(amount_deviation, 5.0),  # Cap at 5x deviation
            "structuring_score": structuring_indicators["score"],
            "near_threshold_count": structuring_indicators["near_threshold_count"]
        }
    
    def _detect_structuring_patterns(
        self, 
        current_amount: float, 
        account_txns: List[Dict[str, Any]], 
        txn_timestamp: datetime
    ) -> Dict[str, float]:
        """Detect potential structuring patterns"""
        
        # Common reporting thresholds
        thresholds = [10000, 5000, 3000, 1000]  # USD equivalents
        structuring_score = 0.0
        near_threshold_count = 0
        
        # Check if current transaction is near thresholds
        for threshold in thresholds:
            if threshold * 0.8 <= current_amount <= threshold * 0.99:
                structuring_score += 0.3
                near_threshold_count += 1
        
        # Check recent transactions for patterns
        recent_window = txn_timestamp - timedelta(days=7)
        recent_txns = [
            txn for txn in account_txns
            if self.parse_timestamp(txn["timestamp"]) >= recent_window
        ]
        
        # Count transactions near thresholds in recent period
        for txn in recent_txns:
            amount = float(txn["amount"])
            for threshold in thresholds:
                if threshold * 0.8 <= amount <= threshold * 0.99:
                    near_threshold_count += 1
                    structuring_score += 0.1
        
        # Multiple small transactions pattern
        if len(recent_txns) >= 5:
            amounts = [float(txn["amount"]) for txn in recent_txns]
            if all(amt < 5000 for amt in amounts) and sum(amounts) > 20000:
                structuring_score += 0.4
        
        return {
            "score": min(structuring_score, 1.0),
            "near_threshold_count": float(near_threshold_count)
        }
    
    def _compute_country_risk_features(self, transaction: Dict[str, Any]) -> Dict[str, float]:
        """Compute enhanced country risk features"""
        
        counterparty_country = transaction.get("counterparty_country", "US")
        country_risk = self.country_risk_scores.get(counterparty_country, 0.5)
        
        # Enhanced risk indicators
        is_sanctions_country = 1.0 if counterparty_country in self.sanctions_countries else 0.0
        is_high_risk_jurisdiction = 1.0 if counterparty_country in self.high_risk_countries else 0.0
        is_tax_haven = 1.0 if counterparty_country in ["KY", "BM", "BS", "BZ", "PA", "CH", "LU", "MC", "LI", "AD"] else 0.0
        
        # Risk level categorization
        risk_level_low = 1.0 if country_risk <= 0.2 else 0.0
        risk_level_medium = 1.0 if 0.2 < country_risk <= 0.6 else 0.0
        risk_level_high = 1.0 if 0.6 < country_risk <= 0.8 else 0.0
        risk_level_critical = 1.0 if country_risk > 0.8 else 0.0
        
        return {
            "country_risk": country_risk,
            "high_risk_country": 1.0 if country_risk >= self.country_risk_high_threshold else 0.0,
            "sanctions_country": is_sanctions_country,
            "high_risk_jurisdiction": is_high_risk_jurisdiction,
            "tax_haven": is_tax_haven,
            "risk_level_low": risk_level_low,
            "risk_level_medium": risk_level_medium,
            "risk_level_high": risk_level_high,
            "risk_level_critical": risk_level_critical,
        }
    
    def _compute_customer_features(
        self,
        transaction: Dict[str, Any],
        customer_store: Dict[str, Any],
        account_store: Dict[str, Any]
    ) -> Dict[str, float]:
        """Compute customer and KYC-related features"""
        
        account_id = transaction["account_id"]
        account_data = account_store.get(account_id, {})
        customer_id = account_data.get("customer_id")
        
        if not customer_id:
            return self._get_default_customer_features()
        
        customer_data = customer_store.get(customer_id, {})
        
        if not customer_data:
            return self._get_default_customer_features()
        
        # KYC features
        kyc_level = customer_data.get("kyc_level", "basic")
        kyc_gap_score = self.kyc_scores.get(kyc_level, 0.5)
        
        # PEP features
        pep_flag = customer_data.get("pep_flag", False)
        pep_exposure = 1.0 if pep_flag else 0.0
        
        # Account age features
        account_opened = account_data.get("opened_at")
        if account_opened:
            try:
                # Handle different timestamp formats
                if '+00:00+00:00' in account_opened:
                    account_opened = account_opened.replace('+00:00+00:00', '+00:00')
                elif account_opened.endswith('Z'):
                    account_opened = account_opened.replace('Z', '+00:00')
                # Remove any remaining duplicate timezone info
                if account_opened.count('+00:00') > 1:
                    account_opened = account_opened.replace('+00:00', '', account_opened.count('+00:00') - 1)
                
                opened_date = datetime.fromisoformat(account_opened)
                txn_date = self.parse_timestamp(transaction["timestamp"])
                account_age_days = (txn_date - opened_date).days
                account_age_score = min(account_age_days / 365.0, 1.0)  # Normalized to 1 year
            except:
                account_age_score = 0.5
        else:
            account_age_score = 0.5
        
        return {
            "kyc_gap_score": kyc_gap_score,
            "pep_exposure": pep_exposure,
            "account_age_score": account_age_score,
            "new_account": 1.0 if account_age_score < 0.1 else 0.0,  # Account < 36 days old
        }
    
    def _compute_time_features(self, transaction: Dict[str, Any]) -> Dict[str, float]:
        """Compute time-based features"""
        
        try:
            # Handle different timestamp formats
            timestamp_str = transaction["timestamp"]
            if '+00:00+00:00' in timestamp_str:
                timestamp_str = timestamp_str.replace('+00:00+00:00', '+00:00')
            elif timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str.replace('Z', '+00:00')
            # Remove any remaining duplicate timezone info
            if timestamp_str.count('+00:00') > 1:
                timestamp_str = timestamp_str.replace('+00:00', '', timestamp_str.count('+00:00') - 1)
            
            txn_timestamp = datetime.fromisoformat(timestamp_str)
            
            # Hour of day (0-23)
            hour = txn_timestamp.hour
            
            # Weekend indicator
            is_weekend = 1.0 if txn_timestamp.weekday() >= 5 else 0.0
            
            # Off-hours indicator (before 8 AM or after 6 PM)
            is_off_hours = 1.0 if hour < 8 or hour > 18 else 0.0
            
            return {
                "hour_of_day": float(hour),
                "is_weekend": is_weekend,
                "is_off_hours": is_off_hours,
            }
            
        except Exception as e:
            logger.error(f"Error computing time features: {e}")
            return {
                "hour_of_day": 12.0,
                "is_weekend": 0.0,
                "is_off_hours": 0.0,
            }
    
    def _get_default_features(self) -> Dict[str, float]:
        """Return default feature values"""
        return {
            "amount": 0.0,
            "amount_log": 0.0,
            "amount_rounded": 0.0,
            "amount_threshold_10k": 0.0,
            "amount_threshold_50k": 0.0,
            "amt_30d": 0.0,
            "count_30d": 0.0,
            "avg_amt_30d": 0.0,
            "amt_7d": 0.0,
            "count_7d": 0.0,
            "velocity_score": 0.0,
            "country_risk": 0.5,
            "high_risk_country": 0.0,
            "kyc_gap_score": 0.5,
            "pep_exposure": 0.0,
            "account_age_score": 0.5,
            "new_account": 0.0,
            "hour_of_day": 12.0,
            "is_weekend": 0.0,
            "is_off_hours": 0.0,
        }
    
    def _get_default_customer_features(self) -> Dict[str, float]:
        """Return default customer feature values"""
        return {
            "kyc_gap_score": 0.5,
            "pep_exposure": 0.0,
            "account_age_score": 0.5,
            "new_account": 0.0,
        } 