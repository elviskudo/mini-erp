"""Schema fixes for Finance module

Revision ID: 62d3d9583387
Revises: 62d3d9583386
Create Date: 2026-01-09

This migration adds missing columns and fixes schema issues for:
- ap_invoices: Added payment_terms, currency_code, exchange_rate, subtotal, 
  tax_amount, notes, amount_paid, amount_due, journal_entry_id, created_at, updated_at
- ap_payments: Changed payment_method from Enum to VARCHAR(50)
- gl_details: Added credit column
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '62d3d9583387'
down_revision: Union[str, None] = '62d3d9583386'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===== AP_INVOICES COLUMNS =====
    # Add missing columns to ap_invoices table
    op.add_column('ap_invoices', sa.Column('payment_terms', sa.String(50), nullable=True))
    op.add_column('ap_invoices', sa.Column('currency_code', sa.String(3), server_default='IDR', nullable=True))
    op.add_column('ap_invoices', sa.Column('exchange_rate', sa.Float, server_default='1.0', nullable=True))
    op.add_column('ap_invoices', sa.Column('subtotal', sa.Float, server_default='0.0', nullable=True))
    op.add_column('ap_invoices', sa.Column('tax_amount', sa.Float, server_default='0.0', nullable=True))
    op.add_column('ap_invoices', sa.Column('notes', sa.Text, nullable=True))
    op.add_column('ap_invoices', sa.Column('amount_paid', sa.Float, server_default='0.0', nullable=True))
    op.add_column('ap_invoices', sa.Column('amount_due', sa.Float, server_default='0.0', nullable=True))
    op.add_column('ap_invoices', sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('ap_invoices', sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=True))
    op.add_column('ap_invoices', sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), nullable=True))
    
    # ===== AP_PAYMENTS COLUMN TYPE CHANGE =====
    # Change payment_method from enum to varchar for flexibility
    op.alter_column('ap_payments', 'payment_method',
                    type_=sa.String(50),
                    existing_type=postgresql.ENUM('CASH', 'QRIS', 'STRIPE', 'CREDIT', name='paymentmethod'),
                    postgresql_using='payment_method::text')
    
    # ===== GL_DETAILS COLUMN =====
    # Add credit column to gl_details (already has debit)
    op.add_column('gl_details', sa.Column('credit', sa.Float, server_default='0.0', nullable=True))


def downgrade() -> None:
    # Remove credit from gl_details
    op.drop_column('gl_details', 'credit')
    
    # Revert payment_method to enum
    op.alter_column('ap_payments', 'payment_method',
                    type_=postgresql.ENUM('CASH', 'QRIS', 'STRIPE', 'CREDIT', name='paymentmethod'),
                    existing_type=sa.String(50),
                    postgresql_using='payment_method::paymentmethod')
    
    # Remove ap_invoices columns
    op.drop_column('ap_invoices', 'updated_at')
    op.drop_column('ap_invoices', 'created_at')
    op.drop_column('ap_invoices', 'journal_entry_id')
    op.drop_column('ap_invoices', 'amount_due')
    op.drop_column('ap_invoices', 'amount_paid')
    op.drop_column('ap_invoices', 'notes')
    op.drop_column('ap_invoices', 'tax_amount')
    op.drop_column('ap_invoices', 'subtotal')
    op.drop_column('ap_invoices', 'exchange_rate')
    op.drop_column('ap_invoices', 'currency_code')
    op.drop_column('ap_invoices', 'payment_terms')
