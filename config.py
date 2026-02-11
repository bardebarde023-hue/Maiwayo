import os
from datetime import timedelta

class Config:
    # JWT Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL = "socialpay.db"
    
    # Transfer Settings
    MAX_TRANSFERS_PER_DAY = 5
    MAX_TRANSFER_AMOUNT = 100000  # ₦100,000
    
    # PIN Settings
    PIN_MAX_ATTEMPTS = 3
    PIN_LOCKOUT_MINUTES = 30
    
    # Withdrawal Settings
    MIN_WITHDRAWAL_NAIRA = 1000
    WITHDRAWAL_FEE_NAIRA = 100
    MIN_WITHDRAWAL_DOLLAR = 1
    WITHDRAWAL_FEE_DOLLAR = 0.10
    
    # Referral Settings
    REFERRAL_REWARD_NAIRA = 30
    REFERRAL_TASKS_REQUIRED = 10
    
    # Admin Settings
    ADMIN_USERNAME = "Ahmerdee"
    ADMIN_PASSWORD = "Ahmerdee4622"
    
    # Support
    SUPPORT_TELEGRAM = "@Socialpaysupport"
    SUPPORT_GROUP = "https://t.me/Socialearningpay"
    SUPPORT_CHANNEL = "https://t.me/socialpaychannel"

config = Config()