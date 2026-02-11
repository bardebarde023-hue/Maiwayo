from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

# ==================== AUTH MODELS ====================

class UserRegister(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str
    referrer_id: Optional[str] = None
    
    @validator('email', 'phone')
    def check_email_or_phone(cls, v, values):
        if not values.get('email') and not values.get('phone'):
            raise ValueError('Either email or phone must be provided')
        return v

class UserLogin(BaseModel):
    identifier: str  # email or phone
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class VerificationRequest(BaseModel):
    identifier: str  # email or phone
    code: str

class ForgotPasswordRequest(BaseModel):
    identifier: str  # email or phone

class ResetPasswordRequest(BaseModel):
    identifier: str
    code: str
    new_password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: Optional[str] = None

# ==================== USER MODELS ====================

class UserProfile(BaseModel):
    user_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    role: str
    is_verified: bool
    referrer_id: Optional[str]
    joined_at: str

class WalletBalance(BaseModel):
    naira: float
    dollar: float
    completed_tasks: int
    pending_tasks: int
    referral_count: int
    referral_naira: float
    referral_dollar: float

class PaymentDetailsInput(BaseModel):
    payment_type: str
    details: str

class PaymentDetailsResponse(BaseModel):
    payment_type: str
    details: str
    updated_at: str

# ==================== TASK MODELS ====================

class TaskCreate(BaseModel):
    platform: str
    task_type: str
    link: str
    currency: str
    price: float
    max_users: int

class TaskResponse(BaseModel):
    task_id: str
    platform: str
    task_type: str
    link: str
    currency: str
    price: float
    status: str
    max_users: int
    completed_count: int
    created_at: str

class TaskSubmission(BaseModel):
    task_id: str
    photo_base64: str  # Base64 encoded image

class SubmissionResponse(BaseModel):
    submission_id: str
    task_id: str
    status: str
    submitted_at: str

# ==================== TRANSFER MODELS ====================

class PINCreate(BaseModel):
    pin: str
    
    @validator('pin')
    def validate_pin(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError('PIN must be exactly 4 digits')
        return v

class TransferRequest(BaseModel):
    receiver_id: str
    amount: float
    pin: str

class TransferResponse(BaseModel):
    transfer_id: str
    from_user: str
    to_user: str
    amount: float
    status: str
    created_at: str

# ==================== WITHDRAWAL MODELS ====================

class WithdrawalRequest(BaseModel):
    currency: str
    amount: float

class WithdrawalResponse(BaseModel):
    withdrawal_id: str
    currency: str
    amount: float
    fee: float
    total: float
    status: str
    requested_at: str

class ExchangeRequest(BaseModel):
    exchange_type: str  # naira_to_dollar or dollar_to_naira
    amount: float

class ExchangeResponse(BaseModel):
    exchange_id: str
    exchange_type: str
    amount: float
    status: str
    requested_at: str

# ==================== ADMIN MODELS ====================

class TaskApproval(BaseModel):
    submission_id: str
    approved: bool

class WithdrawalApproval(BaseModel):
    withdrawal_id: str
    approved: bool

class ExchangeCompletion(BaseModel):
    exchange_id: str
    received_amount: float

class UserManagement(BaseModel):
    user_id: str
    action: str  # ban, unban, adjust_balance
    amount: Optional[float] = None
    currency: Optional[str] = None
    reason: Optional[str] = None

class BroadcastMessage(BaseModel):
    message: str

class TransferReversal(BaseModel):
    log_id: str
    reason: str

class PINReset(BaseModel):
    user_id: str

# ==================== SUPPORT MODELS ====================

class SupportMessage(BaseModel):
    message: str

class SupportReply(BaseModel):
    message_id: str
    reply: str

# ==================== REFERRAL MODELS ====================

class ReferralInfo(BaseModel):
    user_id: str
    name: str
    tasks_completed: int
    reward_paid: bool
    joined_at: str

class ReferralStats(BaseModel):
    total_referrals: int
    earned_naira: float
    earned_dollar: float
    referrals: List[ReferralInfo]

# ==================== RESPONSE MODELS ====================

class SuccessResponse(BaseModel):
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None