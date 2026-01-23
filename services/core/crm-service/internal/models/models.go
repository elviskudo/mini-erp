package models

import (
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// Lead represents a CRM lead
type Lead struct {
	ID                     string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	Name                   string     `gorm:"column:name;not null" json:"name"`
	Company                *string    `gorm:"column:company" json:"company"`
	Email                  *string    `gorm:"column:email" json:"email"`
	Phone                  *string    `gorm:"column:phone" json:"phone"`
	Website                *string    `gorm:"column:website" json:"website"`
	Source                 *string    `gorm:"column:source" json:"source"` // WEBSITE, REFERRAL, SOCIAL_MEDIA, COLD_CALL, EVENT
	Status                 *string    `gorm:"column:status" json:"status"` // NEW, CONTACTED, QUALIFIED, PROPOSAL, NEGOTIATION, WON, LOST
	Industry               *string    `gorm:"column:industry" json:"industry"`
	CompanySize            *string    `gorm:"column:company_size" json:"company_size"`
	Address                *string    `gorm:"column:address" json:"address"`
	Notes                  *string    `gorm:"column:notes" json:"notes"`
	Score                  *int       `gorm:"column:score" json:"score"`
	AssignedTo             *string    `gorm:"column:assigned_to;type:uuid" json:"assigned_to"`
	ConvertedAt            *time.Time `gorm:"column:converted_at" json:"converted_at"`
	ConvertedOpportunityID *string    `gorm:"column:converted_opportunity_id;type:uuid" json:"converted_opportunity_id"`
	ConvertedCustomerID    *string    `gorm:"column:converted_customer_id;type:uuid" json:"converted_customer_id"`
}

func (Lead) TableName() string { return "crm_leads" }

// Customer represents a sales customer
type Customer struct {
	ID             string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID       string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Name           *string    `gorm:"column:name" json:"name"`
	Email          *string    `gorm:"column:email" json:"email"`
	Phone          *string    `gorm:"column:phone" json:"phone"`
	Address        *string    `gorm:"column:address" json:"address"`
	CreditLimit    *float64   `gorm:"column:credit_limit" json:"credit_limit"`
	CurrentBalance *float64   `gorm:"column:current_balance" json:"current_balance"`
	KTPNumber      *string    `gorm:"column:ktp_number" json:"ktp_number"`
	BirthDate      *time.Time `gorm:"column:birth_date" json:"birth_date"`
	CreatedAt      time.Time  `gorm:"column:created_at" json:"created_at"`
	UpdatedAt      time.Time  `gorm:"column:updated_at" json:"updated_at"`
}

func (Customer) TableName() string { return "sales_customers" }

// Opportunity represents a sales opportunity
type Opportunity struct {
	ID                string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID          string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Name              string     `gorm:"column:name;not null" json:"name"`
	Description       *string    `gorm:"column:description" json:"description"`
	Stage             *string    `gorm:"column:stage" json:"stage"` // QUALIFICATION, NEEDS_ANALYSIS, PROPOSAL, NEGOTIATION, CLOSED_WON, CLOSED_LOST
	Probability       *int       `gorm:"column:probability" json:"probability"`
	ExpectedValue     *float64   `gorm:"column:expected_value" json:"expected_value"`
	ExpectedCloseDate *time.Time `gorm:"column:expected_close_date" json:"expected_close_date"`
	LeadID            *string    `gorm:"column:lead_id;type:uuid" json:"lead_id"`
	CustomerID        *string    `gorm:"column:customer_id;type:uuid" json:"customer_id"`
	AssignedTo        *string    `gorm:"column:assigned_to;type:uuid" json:"assigned_to"`
	ClosedAt          *time.Time `gorm:"column:closed_at" json:"closed_at"`
	ActualValue       *float64   `gorm:"column:actual_value" json:"actual_value"`
	LostReason        *string    `gorm:"column:lost_reason" json:"lost_reason"`
	CreatedBy         *string    `gorm:"column:created_by;type:uuid" json:"created_by"`
	CreatedAt         time.Time  `gorm:"column:created_at" json:"created_at"`
	UpdatedAt         time.Time  `gorm:"column:updated_at" json:"updated_at"`
}

func (Opportunity) TableName() string { return "crm_opportunities" }

func (o *Opportunity) BeforeCreate(tx *gorm.DB) (err error) {
	if o.ID == "" {
		o.ID = uuid.New().String()
	}
	return
}

// Activity represents a CRM activity
type Activity struct {
	ID              string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID        string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Title           string     `gorm:"column:title;not null" json:"title"`
	Description     *string    `gorm:"column:description" json:"description"`
	ActivityType    *string    `gorm:"column:activity_type" json:"activity_type"` // CALL, EMAIL, MEETING, TASK
	Status          *string    `gorm:"column:status" json:"status"`               // Planned, In Progress, Completed, Cancelled
	DueDate         *time.Time `gorm:"column:due_date" json:"due_date"`
	DueTime         *string    `gorm:"column:due_time" json:"due_time"`
	DurationMinutes *int       `gorm:"column:duration_minutes" json:"duration_minutes"`
	Priority        *string    `gorm:"column:priority" json:"priority"`
	LeadID          *string    `gorm:"column:lead_id;type:uuid" json:"lead_id"`
	OpportunityID   *string    `gorm:"column:opportunity_id;type:uuid" json:"opportunity_id"`
	CustomerID      *string    `gorm:"column:customer_id;type:uuid" json:"customer_id"`
	AssignedTo      *string    `gorm:"column:assigned_to;type:uuid" json:"assigned_to"`
	CompletedAt     *time.Time `gorm:"column:completed_at" json:"completed_at"`
	Outcome         *string    `gorm:"column:outcome" json:"outcome"`
	CreatedBy       *string    `gorm:"column:created_by;type:uuid" json:"created_by"`
	CreatedAt       time.Time  `gorm:"column:created_at" json:"created_at"`
	UpdatedAt       time.Time  `gorm:"column:updated_at" json:"updated_at"`
}

func (Activity) TableName() string { return "crm_activities" }

func (a *Activity) BeforeCreate(tx *gorm.DB) (err error) {
	if a.ID == "" {
		a.ID = uuid.New().String()
	}
	return
}
