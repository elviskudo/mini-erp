package models

import (
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// CustomerEmail represents email communication with a customer
type CustomerEmail struct {
	ID         string     `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID   string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	CustomerID string     `gorm:"column:customer_id;type:uuid;index;not null" json:"customer_id"`
	Subject    string     `gorm:"column:subject;type:varchar(255);not null" json:"subject"`
	Body       string     `gorm:"column:body;type:text" json:"body"`
	Direction  string     `gorm:"column:direction;type:varchar(10);default:'outgoing'" json:"direction"` // incoming, outgoing
	Status     string     `gorm:"column:status;type:varchar(20);default:'sent'" json:"status"`           // draft, sent, delivered, read
	FromEmail  string     `gorm:"column:from_email;type:varchar(255)" json:"from_email"`
	ToEmail    string     `gorm:"column:to_email;type:varchar(255)" json:"to_email"`
	SentAt     *time.Time `gorm:"column:sent_at" json:"sent_at"`
	CreatedBy  *string    `gorm:"column:created_by;type:uuid" json:"created_by"`
	CreatedAt  time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (CustomerEmail) TableName() string { return "crm_customer_emails" }

// CustomerCall represents a phone call log
type CustomerCall struct {
	ID          string    `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID    string    `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	CustomerID  string    `gorm:"column:customer_id;type:uuid;index;not null" json:"customer_id"`
	ContactID   *string   `gorm:"column:contact_id;type:uuid" json:"contact_id"`
	Direction   string    `gorm:"column:direction;type:varchar(10);default:'outgoing'" json:"direction"` // incoming, outgoing
	PhoneNumber string    `gorm:"column:phone_number;type:varchar(50)" json:"phone_number"`
	Duration    int       `gorm:"column:duration;default:0" json:"duration"`                        // Duration in seconds
	Status      string    `gorm:"column:status;type:varchar(20);default:'completed'" json:"status"` // completed, missed, voicemail
	Notes       string    `gorm:"column:notes;type:text" json:"notes"`
	CallTime    time.Time `gorm:"column:call_time" json:"call_time"`
	CreatedBy   *string   `gorm:"column:created_by;type:uuid" json:"created_by"`
	CreatedAt   time.Time `gorm:"column:created_at" json:"created_at"`
}

func (CustomerCall) TableName() string { return "crm_customer_calls" }

// CustomerMeeting represents a meeting with customer
type CustomerMeeting struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID    string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	CustomerID  string     `gorm:"column:customer_id;type:uuid;index;not null" json:"customer_id"`
	Title       string     `gorm:"column:title;type:varchar(255);not null" json:"title"`
	Description string     `gorm:"column:description;type:text" json:"description"`
	Location    string     `gorm:"column:location;type:varchar(255)" json:"location"`
	MeetingType string     `gorm:"column:meeting_type;type:varchar(20);default:'in_person'" json:"meeting_type"` // in_person, virtual, phone
	StartTime   time.Time  `gorm:"column:start_time" json:"start_time"`
	EndTime     *time.Time `gorm:"column:end_time" json:"end_time"`
	Status      string     `gorm:"column:status;type:varchar(20);default:'scheduled'" json:"status"` // scheduled, completed, cancelled
	Attendees   string     `gorm:"column:attendees;type:text" json:"attendees"`                      // JSON array of attendee names/emails
	Notes       string     `gorm:"column:notes;type:text" json:"notes"`
	CreatedBy   *string    `gorm:"column:created_by;type:uuid" json:"created_by"`
	CreatedAt   time.Time  `gorm:"column:created_at" json:"created_at"`
	UpdatedAt   time.Time  `gorm:"column:updated_at" json:"updated_at"`
}

func (CustomerMeeting) TableName() string { return "crm_customer_meetings" }

// CustomerDocument represents a document associated with customer
type CustomerDocument struct {
	ID          string    `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID    string    `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	CustomerID  string    `gorm:"column:customer_id;type:uuid;index;not null" json:"customer_id"`
	Name        string    `gorm:"column:name;type:varchar(255);not null" json:"name"`
	Description string    `gorm:"column:description;type:text" json:"description"`
	FileType    string    `gorm:"column:file_type;type:varchar(50)" json:"file_type"` // pdf, doc, image, etc
	FileSize    int64     `gorm:"column:file_size" json:"file_size"`
	FilePath    string    `gorm:"column:file_path;type:varchar(500)" json:"file_path"`
	Category    string    `gorm:"column:category;type:varchar(50)" json:"category"` // contract, proposal, invoice, other
	UploadedBy  *string   `gorm:"column:uploaded_by;type:uuid" json:"uploaded_by"`
	CreatedAt   time.Time `gorm:"column:created_at" json:"created_at"`
}

func (CustomerDocument) TableName() string { return "crm_customer_documents" }

func (d *CustomerDocument) BeforeCreate(tx *gorm.DB) (err error) {
	if d.ID == "" {
		d.ID = uuid.New().String()
	}
	return
}
