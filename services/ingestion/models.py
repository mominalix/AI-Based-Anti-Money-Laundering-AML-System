from datetime import datetime, date
from typing import Literal
from pydantic import BaseModel, Field

class Account(BaseModel):
    account_id: str = Field(..., description="Unique account identifier")
    customer_id: str = Field(..., description="Associated customer identifier")
    country: str = Field(..., description="Account country code")
    opened_at: datetime = Field(..., description="Account opening timestamp")
    account_type: Literal["current", "savings", "business", "offshore", "private_banking", "corporate", "checking", "trust"] = Field(..., description="Type of account")

class Customer(BaseModel):
    customer_id: str = Field(..., description="Unique customer identifier")
    full_name: str = Field(..., description="Customer full name")
    dob: date = Field(..., description="Date of birth")
    kyc_level: Literal["basic", "standard", "enhanced"] = Field(..., description="KYC verification level")
    pep_flag: bool = Field(..., description="Politically Exposed Person flag")

class Transaction(BaseModel):
    txn_id: str = Field(..., description="Unique transaction identifier")
    account_id: str = Field(..., description="Associated account identifier")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(..., description="Transaction currency code")
    counterparty_country: str = Field(..., description="Counterparty country code") 