package models

import (
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// EmailBroadcast represents a mass email campaign
type EmailBroadcast struct {
	ID          string     `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	TenantID    string     `gorm:"type:uuid;not null;index" json:"tenant_id"`
	Subject     string     `gorm:"type:text;not null" json:"subject"`
	Body        string     `gorm:"type:text" json:"body"`
	Recipients  string     `gorm:"type:jsonb" json:"recipients"`                   // JSON array of recipients or criteria
	Status      string     `gorm:"type:varchar(20);default:'draft'" json:"status"` // draft, scheduled, sending, sent, failed
	ScheduledAt *time.Time `gorm:"type:timestamptz" json:"scheduled_at"`
	SentAt      *time.Time `gorm:"type:timestamptz" json:"sent_at"`
	Stats       string     `gorm:"type:jsonb" json:"stats"` // JSON for sent count, opened, clicked, bounced
	CreatedBy   *string    `gorm:"type:uuid" json:"created_by"`
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
}

func (EmailBroadcast) TableName() string { return "crm_email_broadcasts" }

func (b *EmailBroadcast) BeforeCreate(tx *gorm.DB) (err error) {
	if b.ID == "" {
		b.ID = uuid.New().String()
	}
	return
}
