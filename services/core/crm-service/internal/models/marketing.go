package models

import (
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// Campaign represents a marketing campaign
type Campaign struct {
	ID             string     `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID       string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Name           string     `gorm:"column:name;not null" json:"name"`
	Description    string     `gorm:"column:description;type:text" json:"description"`
	Type           string     `gorm:"column:type;type:varchar(50)" json:"type"`                     // EMAIL, SOCIAL, EVENT, PAID_ADS, CONTENT
	Status         string     `gorm:"column:status;type:varchar(20);default:'draft'" json:"status"` // draft, active, paused, completed
	StartDate      *time.Time `gorm:"column:start_date" json:"start_date"`
	EndDate        *time.Time `gorm:"column:end_date" json:"end_date"`
	Budget         float64    `gorm:"column:budget;type:decimal(15,2)" json:"budget"`
	SpentAmount    float64    `gorm:"column:spent_amount;type:decimal(15,2);default:0" json:"spent_amount"`
	TargetAudience string     `gorm:"column:target_audience;type:text" json:"target_audience"`
	Goals          string     `gorm:"column:goals;type:text" json:"goals"`
	LeadsGenerated int        `gorm:"column:leads_generated;default:0" json:"leads_generated"`
	Conversions    int        `gorm:"column:conversions;default:0" json:"conversions"`
	CreatedBy      *string    `gorm:"column:created_by;type:uuid" json:"created_by"`
	CreatedAt      time.Time  `gorm:"column:created_at" json:"created_at"`
	UpdatedAt      time.Time  `gorm:"column:updated_at" json:"updated_at"`
}

func (Campaign) TableName() string { return "crm_campaigns" }

// WebForm represents a lead capture form
type WebForm struct {
	ID             string    `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID       string    `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Name           string    `gorm:"column:name;not null" json:"name"`
	Description    string    `gorm:"column:description;type:text" json:"description"`
	Slug           string    `gorm:"column:slug;type:varchar(100);uniqueIndex" json:"slug"` // For URL
	CampaignID     *string   `gorm:"column:campaign_id;type:uuid;index" json:"campaign_id"`
	Status         string    `gorm:"column:status;type:varchar(20);default:'draft'" json:"status"` // draft, active, inactive
	Fields         string    `gorm:"column:fields;type:jsonb" json:"fields"`                       // JSON array of form fields
	SubmitText     string    `gorm:"column:submit_text;type:varchar(50);default:'Submit'" json:"submit_text"`
	SuccessMessage string    `gorm:"column:success_message;type:text" json:"success_message"`
	RedirectURL    *string   `gorm:"column:redirect_url;type:varchar(500)" json:"redirect_url"`
	Submissions    int       `gorm:"column:submissions;default:0" json:"submissions"`
	EmbedCode      string    `gorm:"column:embed_code;type:text" json:"-"` // Generated embed code
	CreatedBy      *string   `gorm:"column:created_by;type:uuid" json:"created_by"`
	CreatedAt      time.Time `gorm:"column:created_at" json:"created_at"`
	UpdatedAt      time.Time `gorm:"column:updated_at" json:"updated_at"`
}

func (WebForm) TableName() string { return "crm_web_forms" }

// WebFormSubmission represents a form submission
type WebFormSubmission struct {
	ID        string    `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	FormID    string    `gorm:"column:form_id;type:uuid;not null;index" json:"form_id"`
	Data      string    `gorm:"column:data;type:jsonb" json:"data"`      // JSON of submitted fields
	LeadID    *string   `gorm:"column:lead_id;type:uuid" json:"lead_id"` // Created lead if any
	IPAddress *string   `gorm:"column:ip_address;type:varchar(50)" json:"ip_address"`
	UserAgent *string   `gorm:"column:user_agent;type:text" json:"user_agent"`
	CreatedAt time.Time `gorm:"column:created_at" json:"created_at"`
}

func (WebFormSubmission) TableName() string { return "crm_web_form_submissions" }

func (s *WebFormSubmission) BeforeCreate(tx *gorm.DB) (err error) {
	if s.ID == "" {
		s.ID = uuid.New().String()
	}
	return
}
