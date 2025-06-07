from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import uuid4

router = APIRouter()

# In-memory database simulation: list of expense dicts with unique IDs
expenses_db = []

class Expense(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), description="Unique ID")
    name: str = Field(..., description="Name of the expense")
    amount: float = Field(..., gt=0, description="Amount spent (greater than 0)")
    date: str = Field(..., regex=r"^\d{4}-\d{2}-\d{2}$", description="Date in YYYY-MM-DD format")
    bought: Optional[bool] = Field(False, description="Whether the item was bought")

@router.post("/add-expense", response_model=Expense)
def add_expense(data: Expense):
    """
    Add a new expense entry.
    """
    expenses_db.append(data.dict())
    return data

@router.get("/expenses", response_model=List[Expense])
def get_all_expenses():
    """
    Get all expenses.
    """
    return expenses_db

@router.get("/total-expense")
def total_expense(bought: Optional[bool] = Query(None, description="Filter by bought status")):
    """
    Calculate total expense. Optionally filter by bought status.
    """
    filtered = expenses_db
    if bought is not None:
        filtered = [item for item in expenses_db if item.get('bought') == bought]
    total = sum(item['amount'] for item in filtered)
    return {"total_expense": total, "entries": filtered}

@router.delete("/expense/{expense_id}")
def delete_expense(expense_id: str):
    """
    Delete an expense by its ID.
    """
    global expenses_db
    original_len = len(expenses_db)
    expenses_db = [item for item in expenses_db if item['id'] != expense_id]
    if len(expenses_db) == original_len:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": f"Expense {expense_id} deleted successfully."}
