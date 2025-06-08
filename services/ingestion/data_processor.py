import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes and validates JSON data from external sources"""
    
    def __init__(self):
        self.processed_batches = {}
        self.data_relationships = {}
        
    async def process_batch_files(
        self, 
        accounts_content: bytes, 
        customers_content: bytes, 
        transactions_content: bytes
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Process and validate batch files, establishing relationships
        
        Returns:
            Tuple of (accounts, customers, transactions) with enriched data
        """
        
        try:
            # Parse JSON content
            accounts_data = json.loads(accounts_content.decode('utf-8'))
            customers_data = json.loads(customers_content.decode('utf-8'))
            transactions_data = json.loads(transactions_content.decode('utf-8'))
            
            # Validate data structure
            self._validate_data_structure(accounts_data, customers_data, transactions_data)
            
            # Build relationship mappings
            customer_map = {customer["customer_id"]: customer for customer in customers_data}
            account_map = {account["account_id"]: account for account in accounts_data}
            
            # Enrich data with relationships
            enriched_accounts = self._enrich_accounts(accounts_data, customer_map)
            enriched_customers = self._enrich_customers(customers_data, account_map)
            enriched_transactions = self._enrich_transactions(transactions_data, account_map, customer_map)
            
            # Validate business rules
            self._validate_business_rules(enriched_accounts, enriched_customers, enriched_transactions)
            
            logger.info(f"Processed batch: {len(enriched_accounts)} accounts, {len(enriched_customers)} customers, {len(enriched_transactions)} transactions")
            
            return enriched_accounts, enriched_customers, enriched_transactions
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"Error processing batch files: {e}")
            raise
    
    def _validate_data_structure(self, accounts: List[Dict], customers: List[Dict], transactions: List[Dict]):
        """Validate the structure of input data"""
        
        # Required fields for each entity type
        required_account_fields = {"account_id", "customer_id", "country", "opened_at", "account_type"}
        required_customer_fields = {"customer_id", "full_name", "dob", "kyc_level", "pep_flag"}
        required_transaction_fields = {"txn_id", "account_id", "timestamp", "amount", "currency", "counterparty_country"}
        
        # Validate accounts
        for i, account in enumerate(accounts):
            missing_fields = required_account_fields - set(account.keys())
            if missing_fields:
                logger.warning(f"Account {i}: Missing fields: {missing_fields}")
        
        # Validate customers
        for i, customer in enumerate(customers):
            missing_fields = required_customer_fields - set(customer.keys())
            if missing_fields:
                logger.warning(f"Customer {i}: Missing fields: {missing_fields}")
        
        # Validate transactions
        for i, transaction in enumerate(transactions):
            missing_fields = required_transaction_fields - set(transaction.keys())
            if missing_fields:
                logger.warning(f"Transaction {i}: Missing fields: {missing_fields}")
    
    def _enrich_accounts(self, accounts: List[Dict], customer_map: Dict[str, Dict]) -> List[Dict]:
        """Enrich account data with customer information"""
        
        enriched_accounts = []
        
        for account in accounts:
            enriched_account = account.copy()
            
            # Add customer information
            customer_id = account.get("customer_id", "")
            if customer_id in customer_map:
                customer = customer_map[customer_id]
                enriched_account["customer_name"] = customer.get("full_name", "Unknown")
                enriched_account["customer_pep_flag"] = customer.get("pep_flag", False)
                enriched_account["customer_kyc_level"] = customer.get("kyc_level", "basic")
                enriched_account["customer_dob"] = customer.get("dob", None)
            else:
                logger.warning(f"Customer {customer_id} not found for account {account.get('account_id')}")
                enriched_account["customer_name"] = "Unknown"
                enriched_account["customer_pep_flag"] = False
                enriched_account["customer_kyc_level"] = "basic"
                enriched_account["customer_dob"] = None
            
            # Calculate account age
            try:
                opened_date = datetime.fromisoformat(account["opened_at"].replace('Z', '+00:00'))
                account_age_days = (datetime.utcnow() - opened_date).days
                enriched_account["account_age_days"] = account_age_days
                enriched_account["account_age_years"] = round(account_age_days / 365.25, 2)
            except:
                enriched_account["account_age_days"] = 0
                enriched_account["account_age_years"] = 0
            
            enriched_accounts.append(enriched_account)
        
        return enriched_accounts
    
    def _enrich_customers(self, customers: List[Dict], account_map: Dict[str, Dict]) -> List[Dict]:
        """Enrich customer data with account information"""
        
        enriched_customers = []
        
        for customer in customers:
            enriched_customer = customer.copy()
            
            # Find customer's accounts
            customer_accounts = [
                account for account in account_map.values() 
                if account.get("customer_id") == customer.get("customer_id")
            ]
            
            enriched_customer["account_count"] = len(customer_accounts)
            enriched_customer["account_types"] = list(set(acc.get("account_type", "unknown") for acc in customer_accounts))
            enriched_customer["account_countries"] = list(set(acc.get("country", "unknown") for acc in customer_accounts))
            
            # Calculate customer age
            try:
                birth_date = datetime.strptime(customer["dob"], "%Y-%m-%d")
                age_years = (datetime.now() - birth_date).days / 365.25
                enriched_customer["age_years"] = round(age_years, 1)
            except:
                enriched_customer["age_years"] = None
            
            enriched_customers.append(enriched_customer)
        
        return enriched_customers
    
    def _enrich_transactions(
        self, 
        transactions: List[Dict], 
        account_map: Dict[str, Dict], 
        customer_map: Dict[str, Dict]
    ) -> List[Dict]:
        """Enrich transaction data with account and customer information"""
        
        enriched_transactions = []
        
        for transaction in transactions:
            enriched_transaction = transaction.copy()
            
            # Add account information
            account_id = transaction.get("account_id", "")
            if account_id in account_map:
                account = account_map[account_id]
                enriched_transaction["account_country"] = account.get("country", "Unknown")
                enriched_transaction["account_type"] = account.get("account_type", "unknown")
                enriched_transaction["customer_id"] = account.get("customer_id", "Unknown")
                
                # Add customer information
                customer_id = account.get("customer_id", "")
                if customer_id in customer_map:
                    customer = customer_map[customer_id]
                    enriched_transaction["customer_name"] = customer.get("full_name", "Unknown")
                    enriched_transaction["customer_pep_flag"] = customer.get("pep_flag", False)
                    enriched_transaction["customer_kyc_level"] = customer.get("kyc_level", "basic")
                else:
                    enriched_transaction["customer_name"] = "Unknown"
                    enriched_transaction["customer_pep_flag"] = False
                    enriched_transaction["customer_kyc_level"] = "basic"
            else:
                logger.warning(f"Account {account_id} not found for transaction {transaction.get('txn_id')}")
                enriched_transaction["account_country"] = "Unknown"
                enriched_transaction["account_type"] = "unknown"
                enriched_transaction["customer_id"] = "Unknown"
                enriched_transaction["customer_name"] = "Unknown"
                enriched_transaction["customer_pep_flag"] = False
                enriched_transaction["customer_kyc_level"] = "basic"
            
            # Add transaction metadata
            try:
                txn_timestamp = datetime.fromisoformat(transaction["timestamp"].replace('Z', '+00:00'))
                enriched_transaction["transaction_date"] = txn_timestamp.date().isoformat()
                enriched_transaction["transaction_hour"] = txn_timestamp.hour
                enriched_transaction["is_weekend"] = txn_timestamp.weekday() >= 5
                enriched_transaction["is_off_hours"] = txn_timestamp.hour < 8 or txn_timestamp.hour > 18
            except:
                enriched_transaction["transaction_date"] = None
                enriched_transaction["transaction_hour"] = 12
                enriched_transaction["is_weekend"] = False
                enriched_transaction["is_off_hours"] = False
            
            enriched_transactions.append(enriched_transaction)
        
        return enriched_transactions
    
    def _validate_business_rules(self, accounts: List[Dict], customers: List[Dict], transactions: List[Dict]):
        """Validate business rules across the dataset"""
        
        # Check for orphaned transactions
        account_ids = {account.get("account_id") for account in accounts}
        orphaned_transactions = [
            txn for txn in transactions 
            if txn.get("account_id") not in account_ids
        ]
        
        if orphaned_transactions:
            logger.warning(f"Found {len(orphaned_transactions)} orphaned transactions")
        
        # Check for orphaned accounts
        customer_ids = {customer.get("customer_id") for customer in customers}
        orphaned_accounts = [
            acc for acc in accounts 
            if acc.get("customer_id") not in customer_ids
        ]
        
        if orphaned_accounts:
            logger.warning(f"Found {len(orphaned_accounts)} orphaned accounts") 