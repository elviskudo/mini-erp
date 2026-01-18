package models

import (
	"time"

	"github.com/shopspring/decimal"
)

// ChartOfAccount represents an account in the chart of accounts (matches migrated DB)
type ChartOfAccount struct {
	ID          string  `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string  `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Code        string  `gorm:"column:code;size:50;index" json:"code"`
	Name        string  `gorm:"column:name;size:255" json:"name"`
	Type        string  `gorm:"column:type;size:50" json:"type"` // ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
	ParentID    *string `gorm:"column:parent_id;type:uuid" json:"parent_id"`
	IsActive    *bool   `gorm:"column:is_active" json:"is_active"`
	Description *string `gorm:"column:description" json:"description"`
}

func (ChartOfAccount) TableName() string {
	return "chart_of_accounts"
}

// GLEntry represents a general ledger entry (matches migrated DB)
type GLEntry struct {
	ID           string          `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID     string          `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	EntryNumber  string          `gorm:"column:entry_number;size:50" json:"entry_number"`
	EntryDate    time.Time       `gorm:"column:entry_date;type:date" json:"entry_date"`
	Description  *string         `gorm:"column:description" json:"description"`
	Reference    *string         `gorm:"column:reference" json:"reference"`
	SourceModule *string         `gorm:"column:source_module;size:50" json:"source_module"`
	SourceID     *string         `gorm:"column:source_id;type:uuid" json:"source_id"`
	Status       string          `gorm:"column:status;size:20" json:"status"`
	TotalDebit   decimal.Decimal `gorm:"column:total_debit;type:decimal(18,2)" json:"total_debit"`
	TotalCredit  decimal.Decimal `gorm:"column:total_credit;type:decimal(18,2)" json:"total_credit"`
	PostedAt     *time.Time      `gorm:"column:posted_at" json:"posted_at"`
	PostedBy     *string         `gorm:"column:posted_by;type:uuid" json:"posted_by"`
	CreatedAt    time.Time       `gorm:"column:created_at" json:"created_at"`
	UpdatedAt    time.Time       `gorm:"column:updated_at" json:"updated_at"`
}

func (GLEntry) TableName() string {
	return "gl_entries"
}

// GLDetail represents a line item in a GL entry
type GLDetail struct {
	ID          string          `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	GLEntryID   string          `gorm:"column:gl_entry_id;type:uuid;index;not null" json:"gl_entry_id"`
	AccountID   string          `gorm:"column:account_id;type:uuid;index;not null" json:"account_id"`
	Description *string         `gorm:"column:description" json:"description"`
	Debit       decimal.Decimal `gorm:"column:debit;type:decimal(18,2)" json:"debit"`
	Credit      decimal.Decimal `gorm:"column:credit;type:decimal(18,2)" json:"credit"`
}

func (GLDetail) TableName() string {
	return "gl_details"
}

// BankAccount represents a company bank account (matches migrated DB)
type BankAccount struct {
	ID            string          `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID      string          `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	AccountName   string          `gorm:"column:account_name;size:255" json:"account_name"`
	AccountNumber string          `gorm:"column:account_number;size:50" json:"account_number"`
	BankName      string          `gorm:"column:bank_name;size:100" json:"bank_name"`
	BranchName    *string         `gorm:"column:branch_name;size:100" json:"branch_name"`
	Currency      string          `gorm:"column:currency;size:3;default:IDR" json:"currency"`
	Balance       decimal.Decimal `gorm:"column:balance;type:decimal(18,2)" json:"balance"`
	GLAccountID   *string         `gorm:"column:gl_account_id;type:uuid" json:"gl_account_id"`
	IsActive      *bool           `gorm:"column:is_active" json:"is_active"`
	CreatedAt     time.Time       `gorm:"column:created_at" json:"created_at"`
	UpdatedAt     time.Time       `gorm:"column:updated_at" json:"updated_at"`
}

func (BankAccount) TableName() string {
	return "bank_accounts"
}
