from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import sqlite3
import secrets
import base64
import os

from app.database import get_db
from app.auth import get_current_user
from app.models import *

router = APIRouter()

@router.get("/available")
async def get_available_tasks(
    platform: str = None,
    task_type: str = None,
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    
    query = """
        SELECT t.*, 
               (SELECT COUNT(*) FROM task_completions WHERE task_id = t.task_id) as completed_count
        FROM tasks t
        WHERE t.status = 'active'
    """
    params = []
    
    if platform:
        query += " AND t.platform = ?"
        params.append(platform)
    
    if task_type:
        query += " AND t.task_type = ?"
        params.append(task_type)
    
    cursor.execute(query, params)
    tasks = cursor.fetchall()
    
    available_tasks = []
    for task in tasks:
        cursor.execute("SELECT * FROM task_completions WHERE task_id = ? AND user_id = ?", 
                       (task['task_id'], current_user['user_id']))
        if cursor.fetchone():
            continue
        
        if task['completed_count'] >= task['max_users']:
            continue
        
        available_tasks.append({
            "task_id": task['task_id'],
            "platform": task['platform'],
            "task_type": task['task_type'],
            "link": task['link'],
            "currency": task['currency'],
            "price": task['price_naira'] if task['currency'] == 'naira' else task['price_dollar'],
            "completed_count": task['completed_count'],
            "max_users": task['max_users']
        })
    
    return {"tasks": available_tasks}

@router.post("/submit", response_model=SubmissionResponse)
async def submit_task(
    submission: TaskSubmission,
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    
    # Check if task exists
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (submission.task_id,))
    task = cursor.fetchone()
    
    if not task or task['status'] != 'active':
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if already submitted
    cursor.execute("SELECT * FROM submissions WHERE task_id = ? AND user_id = ?", 
                   (submission.task_id, current_user['user_id']))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Task already submitted")
    
    # Save image
    image_data = base64.b64decode(submission.photo_base64)
    os.makedirs("uploads", exist_ok=True)
    filename = f"{current_user['user_id']}_{submission.task_id}_{int(datetime.now().timestamp())}.jpg"
    filepath = f"uploads/{filename}"
    
    with open(filepath, "wb") as f:
        f.write(image_data)
    
    # Create submission
    submission_id = f"sub_{current_user['user_id']}_{submission.task_id}_{int(datetime.now().timestamp())}"
    
    cursor.execute("""
        INSERT INTO submissions (submission_id, user_id, task_id, photo_url, submitted_at)
        VALUES (?, ?, ?, ?, ?)
    """, (submission_id, current_user['user_id'], submission.task_id, filepath, datetime.now().isoformat()))
    
    # Update pending tasks
    cursor.execute("UPDATE wallets SET pending_tasks = pending_tasks + 1 WHERE user_id = ?", 
                   (current_user['user_id'],))
    
    db.commit()
    
    return SubmissionResponse(
        submission_id=submission_id,
        task_id=submission.task_id,
        status="pending",
        submitted_at=datetime.now().isoformat()
    )

@router.get("/my-submissions")
async def get_my_submissions(current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT s.*, t.platform, t.task_type, t.currency, t.price_naira, t.price_dollar
        FROM submissions s
        JOIN tasks t ON s.task_id = t.task_id
        WHERE s.user_id = ?
        ORDER BY s.submitted_at DESC
    """, (current_user['user_id'],))
    
    submissions = cursor.fetchall()
    
    result = []
    for sub in submissions:
        result.append({
            "submission_id": sub['submission_id'],
            "task_id": sub['task_id'],
            "platform": sub['platform'],
            "task_type": sub['task_type'],
            "price": sub['price_naira'] if sub['currency'] == 'naira' else sub['price_dollar'],
            "currency": sub['currency'],
            "status": sub['status'],
            "submitted_at": sub['submitted_at']
        })
    
    return {"submissions": result}