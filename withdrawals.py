from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import sqlite3
import secrets

from app.database import get_db
from app.auth import get_current_user
from app.models import *
from app.config import config

router = APIRouter()

@router.post("/request", response_model=WithdrawalResponse)
async def request_withdrawal(
    request: WithdrawalRequest,
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    
    # Check payment details
    cursor.execute("SELECT * FROM payment_details WHERE user_id = ?", (current_user['user_id'],))
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Payment details not set")
    
    # Get wallet
    cursor.execute("SELECT * FROM wallets WHERE user_id = ?", (current_user['user_id'],))
    wallet = cursor.fetchone()
    
    # Calculate fee and total
    if request.currency == "naira":
        min_amount = config.MIN_WITHDRAWAL_NAIRA
        fee = config.WITHDRAWAL_FEE_NAIRA
        balance = wallet['naira']
    else:
        min_amount = config.MIN_WITHDRAWAL_DOLLAR
        fee = config.WITHDRAWAL_FEE_DOLLAR
        balance = wallet['dollar']
    
    if request.amount < min_amount:
        raise HTTPException(status_code=400, detail=f"Minimum withdrawal is {min_amount}")
    
    total = request.amount + fee
    
    if balance < total:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Deduct from wallet
    if request.currency == "naira":
        cursor.execute("UPDATE wallets SET naira = naira - ? WHERE user_id = ?", 
                       (total, current_user['user_id']))
    else:
        cursor.execute("UPDATE wallets SET dollar = dollar - ? WHERE user_id = ?", 
                       (total, current_user['user_id']))
    
    # Create withdrawal request
    withdrawal_id = f"wd_{current_user['user_id']}_{int(datetime.now().timestamp())}"
    
    cursor.execute("""
        INSERT INTO withdrawals (withdrawal_id, user_id, currency, amount, fee, total, requested_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (withdrawal_id, current_user['user_id'], request.currency, request.amount, fee, total, 
          datetime.now().isoformat()))
    
    db.commit()
    
    return WithdrawalResponse(
        withdrawal_id=withdrawal_id,
        currency=request.currency,
        amount=request.amount,
        fee=fee,
        total=total,
        status="pending",
        requested_at=datetime.now().isoformat()
    )

@router.get("/my-withdrawals")
async def get_my_withdrawals(current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT * FROM withdrawals 
        WHERE user_id = ?
        ORDER BY requested_at DESC
    """, (current_user['user_id'],))
    
    withdrawals = cursor.fetchall()
    
    result = []
    for w in withdrawals:
        result.append({
            "withdrawal_id": w['withdrawal_id'],
            "currency": w['currency'],
            "amount": w['amount'],
            "fee": w['fee'],
            "total": w['total'],
            "status": w['status'],
            "requested_at": w['requested_at'],
            "approved_at": w['approved_at']
        })
    
    return {"withdrawals": result}

@router.post("/exchange", response_model=ExchangeResponse)
async def request_exchange(
    request: ExchangeRequest,
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM wallets WHERE user_id = ?", (current_user['user_id'],))
    wallet = cursor.fetchone()
    
    if request.exchange_type == "naira_to_dollar":
        if wallet['naira'] < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient naira balance")
    else:
        if wallet['dollar'] < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient dollar balance")
    
    exchange_id = f"ex_{current_user['user_id']}_{int(datetime.now().timestamp())}"
    
    cursor.execute("""
        INSERT INTO exchanges (exchange_id, user_id, exchange_type, amount, requested_at)
        VALUES (?, ?, ?, ?, ?)
    """, (exchange_id, current_user['user_id'], request.exchange_type, request.amount, 
          datetime.now().isoformat()))
    
    db.commit()
    
    return ExchangeResponse(
        exchange_id=exchange_id,
        exchange_type=request.exchange_type,
        amount=request.amount,
        status="pending",
        requested_at=datetime.now().isoformat()
    )