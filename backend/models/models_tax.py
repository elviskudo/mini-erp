"""
Tax Management Models
Supports Indonesia (PPN, PPh) and International (VAT, GST)
"""
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum


class TaxType(str, enum.Enum):
    """Tax types for Indonesia and International"""
    # Indonesia
    PPN = "PPN"           # Pajak Pertambahan Nilai (VAT)
    PPH21 = "PPH21"       # Pajak Penghasilan Pasal 21 (Employee Income Tax)
    PPH22 = "PPH22"       # Pajak Penghasilan Pasal 22 (Import/Export)
    PPH23 = "PPH23"       # Pajak Penghasilan Pasal 23 (Services, Rent, etc)
    PPH25 = "PPH25"       # Pajak Penghasilan Pasal 25 (Corporate Installment)
    PPH26 = "PPH26"       # Pajak Penghasilan Pasal 26 (Foreign Payments)
    PPH4_2 = "PPH4_2"     # Pajak Penghasilan Pasal 4(2) (Final Tax)
    # International
    VAT = "VAT"           # Value Added Tax
    GST = "GST"           # Goods and Services Tax
    WHT = "WHT"           # Withholding Tax
    SALES_TAX = "SALES_TAX"


class TaxCode(Base):
    """Tax codes configuration - reusable tax definitions"""
    __tablename__ = "tax_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    code = Column(String(20), nullable=False, index=True)  # e.g. "PPN-11", "VAT-10"
    name = Column(String(100), nullable=False)  # e.g. "PPN 11%", "VAT Standard Rate"
    tax_type = Column(Enum(TaxType), nullable=False)
    rate = Column(Float, nullable=False)  # Percentage, e.g. 11.0 for 11%
    
    # Account links for GL entries
    tax_payable_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    tax_receivable_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaxTransaction(Base):
    """Tax transaction records for reporting"""
    __tablename__ = "tax_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    tax_code_id = Column(UUID(as_uuid=True), ForeignKey("tax_codes.id"), nullable=False)
    
    # Transaction reference
    reference_type = Column(String(50))  # "sales_invoice", "purchase_invoice", "payroll", etc.
    reference_id = Column(UUID(as_uuid=True), nullable=True)  # ID of the related document
    reference_number = Column(String(50))  # e.g. "INV-001"
    
    # Tax amounts
    tax_base = Column(Float, default=0.0)  # Amount before tax (DPP)
    tax_amount = Column(Float, default=0.0)  # Tax amount
    
    # Counterparty
    counterparty_type = Column(String(20))  # "customer" or "vendor"
    counterparty_id = Column(UUID(as_uuid=True), nullable=True)
    counterparty_name = Column(String(200))
    counterparty_npwp = Column(String(30))  # Tax ID (NPWP for Indonesia)
    
    transaction_date = Column(DateTime, nullable=False)
    is_input_tax = Column(Boolean, default=False)  # True = input (can be credited), False = output
    
    # Journal link
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tax_code = relationship("TaxCode")


class EFaktur(Base):
    """e-Faktur records for Indonesia tax compliance"""
    __tablename__ = "efaktur"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # e-Faktur number format: 010.000-00.00000001
    nomor_faktur = Column(String(30), nullable=False, unique=True, index=True)
    
    # Reference to tax transaction
    tax_transaction_id = Column(UUID(as_uuid=True), ForeignKey("tax_transactions.id"), nullable=True)
    
    # e-Faktur data
    kode_transaksi = Column(String(2))  # 01, 02, 03, etc.
    tanggal_faktur = Column(DateTime, nullable=False)
    
    # Seller (PKP) info
    npwp_penjual = Column(String(20))
    nama_penjual = Column(String(200))
    alamat_penjual = Column(Text)
    
    # Buyer info
    npwp_pembeli = Column(String(20))
    nama_pembeli = Column(String(200))
    alamat_pembeli = Column(Text)
    
    # Amounts
    dpp = Column(Float, default=0.0)  # Dasar Pengenaan Pajak
    ppn = Column(Float, default=0.0)  # PPN amount
    ppnbm = Column(Float, default=0.0)  # Pajak Penjualan Barang Mewah
    
    # Status
    status = Column(String(20), default="draft")  # draft, approved, reported, cancelled
    
    # For export/reporting
    is_exported = Column(Boolean, default=False)
    export_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tax_transaction = relationship("TaxTransaction")


class WithholdingTax(Base):
    """Withholding tax records (PPh 21, 23, 26, etc. for Indonesia; WHT for international)"""
    __tablename__ = "withholding_taxes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    tax_code_id = Column(UUID(as_uuid=True), ForeignKey("tax_codes.id"), nullable=False)
    
    # The party from whom tax is withheld
    withheld_from_type = Column(String(20))  # "employee", "vendor", etc.
    withheld_from_id = Column(UUID(as_uuid=True), nullable=True)
    withheld_from_name = Column(String(200))
    withheld_from_npwp = Column(String(30))
    
    # Reference
    reference_type = Column(String(50))  # "payroll", "vendor_payment", etc.
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    reference_number = Column(String(50))
    
    # Amounts
    gross_amount = Column(Float, default=0.0)  # Amount before withholding
    tax_rate = Column(Float, default=0.0)  # Applied rate
    tax_amount = Column(Float, default=0.0)  # Withheld amount
    net_amount = Column(Float, default=0.0)  # Amount after withholding
    
    transaction_date = Column(DateTime, nullable=False)
    period_month = Column(String(7))  # e.g. "2026-01" for monthly reporting
    
    # Bukti Potong number (for Indonesia)
    bukti_potong_number = Column(String(50), nullable=True)
    
    # Journal link
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("gl_entries.id"), nullable=True)
    
    # For e-Bupot (Indonesia electronic withholding slip)
    is_reported = Column(Boolean, default=False)
    reported_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tax_code = relationship("TaxCode")
