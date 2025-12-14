from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import models
from datetime import datetime
from typing import Dict, List, Any

async def generate_trial_balance(db: AsyncSession) -> List[Dict[str, Any]]:
    # Get all accounts
    result = await db.execute(select(models.ChartOfAccount))
    accounts = result.scalars().all()
    
    report = []
    total_debit = 0.0
    total_credit = 0.0
    
    for account in accounts:
        # Sum GL Details for this account
        # Note: In a real large-scale ERP, this would be pre-calculated in a 'PeriodBalance' table
        stmt = select(
            func.sum(models.JournalDetail.debit),
            func.sum(models.JournalDetail.credit)
        ).where(models.JournalDetail.account_id == account.id)
        
        sums = await db.execute(stmt)
        debit_sum, credit_sum = sums.one()
        
        debit_sum = debit_sum or 0.0
        credit_sum = credit_sum or 0.0
        
        balance = debit_sum - credit_sum
        
        # Determine if it's naturally debit or credit
        # Asset/Expense -> Debit normal
        # Liab/Equity/Income -> Credit normal
        
        if debit_sum == 0 and credit_sum == 0:
            continue
            
        report.append({
            "account_code": account.code,
            "account_name": account.name,
            "debit": debit_sum,
            "credit": credit_sum,
            "net_balance": balance
        })
        
        total_debit += debit_sum
        total_credit += credit_sum
        
    return {
        "lines": report,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": abs(total_debit - total_credit) < 0.01
    }

async def generate_pl(db: AsyncSession, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    # Revenue - Expenses
    # Filter by Date
    
    # 1. Get Income Accounts
    income_accs = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.type == models.AccountType.INCOME))
    expense_accs = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.type == models.AccountType.EXPENSE))
    
    income_accs = income_accs.scalars().all()
    expense_accs = expense_accs.scalars().all()
    
    revenue_lines = []
    total_revenue = 0.0
    
    for acc in income_accs:
        # For Income, Credit is positive
        stmt = select(
            func.sum(models.JournalDetail.credit) - func.sum(models.JournalDetail.debit)
        ).join(models.JournalDetail.entry).where(
            models.JournalDetail.account_id == acc.id,
            models.JournalEntry.date >= start_date,
            models.JournalEntry.date <= end_date
        )
        res = await db.execute(stmt)
        val = res.scalar() or 0.0
        if val != 0:
            revenue_lines.append({"name": acc.name, "amount": val})
            total_revenue += val
            
    expense_lines = []
    total_expense = 0.0
    
    for acc in expense_accs:
        # For Expense, Debit is positive
        stmt = select(
            func.sum(models.JournalDetail.debit) - func.sum(models.JournalDetail.credit)
        ).join(models.JournalDetail.entry).where(
            models.JournalDetail.account_id == acc.id,
            models.JournalEntry.date >= start_date,
            models.JournalEntry.date <= end_date
        )
        res = await db.execute(stmt)
        val = res.scalar() or 0.0
        if val != 0:
            expense_lines.append({"name": acc.name, "amount": val})
            total_expense += val
            
    return {
        "revenue": revenue_lines,
        "expenses": expense_lines,
        "total_revenue": total_revenue,
        "total_expenses": total_expense,
        "net_income": total_revenue - total_expense
    }

async def generate_balance_sheet(db: AsyncSession, as_of_date: datetime) -> Dict[str, Any]:
    # Assets = Liabilities + Equity
    # Net Income from *all time* (or Retained Earnings) must be added to Equity
    
    # Calculate Net Income (Retained Earnings) up to as_of
    # Usually this is done by checking P&L from beginning of time? Or assuming closed periods moved to Retained Earnings.
    # For this MVP, let's calculate Net Income on fly involving all Income/Expense accounts up to as_of_date
    
    # P&L Logic for Retained Earnings
    re_stmt = select(
        func.sum(models.JournalDetail.credit) - func.sum(models.JournalDetail.debit)
    ).join(models.JournalDetail.entry).join(models.JournalDetail.account).where(
        models.JournalEntry.date <= as_of_date,
        (models.ChartOfAccount.type == models.AccountType.INCOME) | (models.ChartOfAccount.type == models.AccountType.EXPENSE)
         # Note: For Expense, Debit is positive, so (Credit - Debit) would be negative, which is correct for 'Income' contribution
         # e.g. Rev 100 (Cr), Exp 50 (Dr). Sum(Cr-Dr) = (100-0) + (0-50) = 50. Correct.
    )
    re_res = await db.execute(re_stmt)
    retained_earnings = re_res.scalar() or 0.0
    
    # ASSETS
    assets = []
    total_assets = 0.0
    asset_accs = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.type == models.AccountType.ASSET))
    for acc in asset_accs.scalars().all():
        # Debit - Credit
        stmt = select(func.sum(models.JournalDetail.debit) - func.sum(models.JournalDetail.credit)).join(models.JournalDetail.entry).where(
            models.JournalDetail.account_id == acc.id,
            models.JournalEntry.date <= as_of_date
        )
        val = (await db.execute(stmt)).scalar() or 0.0
        if val != 0:
            assets.append({"name": acc.name, "amount": val})
            total_assets += val
            
    # LIABILITIES
    liabs = []
    total_liabs = 0.0
    liab_accs = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.type == models.AccountType.LIABILITY))
    for acc in liab_accs.scalars().all():
        # Credit - Debit
        stmt = select(func.sum(models.JournalDetail.credit) - func.sum(models.JournalDetail.debit)).join(models.JournalDetail.entry).where(
            models.JournalDetail.account_id == acc.id,
            models.JournalEntry.date <= as_of_date
        )
        val = (await db.execute(stmt)).scalar() or 0.0
        if val != 0:
            liabs.append({"name": acc.name, "amount": val})
            total_liabs += val
            
    # EQUITY
    equity = []
    total_equity = 0.0
    equity_accs = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.type == models.AccountType.EQUITY))
    for acc in equity_accs.scalars().all():
        # Credit - Debit
        stmt = select(func.sum(models.JournalDetail.credit) - func.sum(models.JournalDetail.debit)).join(models.JournalDetail.entry).where(
            models.JournalDetail.account_id == acc.id,
            models.JournalEntry.date <= as_of_date
        )
        val = (await db.execute(stmt)).scalar() or 0.0
        if val != 0:
            equity.append({"name": acc.name, "amount": val})
            total_equity += val
            
    # Add Retained Earnings to Equity Section
    equity.append({"name": "Retained Earnings (Net Income)", "amount": retained_earnings})
    total_equity += retained_earnings
    
    return {
        "assets": assets,
        "liabilities": liabs,
        "equity": equity,
        "total_assets": total_assets,
        "total_liabilities_equity": total_liabs + total_equity,
        "is_balanced": abs(total_assets - (total_liabs + total_equity)) < 0.01
    }
