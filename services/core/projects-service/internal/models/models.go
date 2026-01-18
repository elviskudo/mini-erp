package models

import "time"

// Project represents a project
type Project struct {
	ID            string     `gorm:"column:id;primaryKey" json:"id"`
	TenantID      string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Name          string     `gorm:"column:name;not null" json:"name"`
	Code          *string    `gorm:"column:code" json:"code"`
	Type          *string    `gorm:"column:type" json:"type"`     // INTERNAL, EXTERNAL, RESEARCH
	Status        *string    `gorm:"column:status" json:"status"` // PLANNING, IN_PROGRESS, ON_HOLD, COMPLETED, CANCELLED
	StartDate     *time.Time `gorm:"column:start_date" json:"start_date"`
	EndDate       *time.Time `gorm:"column:end_date" json:"end_date"`
	Budget        *float64   `gorm:"column:budget" json:"budget"`
	Description   *string    `gorm:"column:description" json:"description"`
	Priority      *string    `gorm:"column:priority" json:"priority"` // LOW, MEDIUM, HIGH, CRITICAL
	ManagerID     *string    `gorm:"column:manager_id;type:uuid" json:"manager_id"`
	ClientID      *string    `gorm:"column:client_id;type:uuid" json:"client_id"`
	ActualEndDate *time.Time `gorm:"column:actual_end_date" json:"actual_end_date"`
	CreatedAt     time.Time  `gorm:"column:created_at" json:"created_at"`
	UpdatedAt     time.Time  `gorm:"column:updated_at" json:"updated_at"`
}

func (Project) TableName() string { return "projects" }

// ProjectTask represents a task within a project
type ProjectTask struct {
	ID             string     `gorm:"column:id;primaryKey" json:"id"`
	TenantID       string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	ProjectID      string     `gorm:"column:project_id;not null" json:"project_id"`
	Name           string     `gorm:"column:name;not null" json:"name"`
	WBSCode        *string    `gorm:"column:wbs_code" json:"wbs_code"`
	ParentID       *string    `gorm:"column:parent_id" json:"parent_id"`
	StartDate      *time.Time `gorm:"column:start_date" json:"start_date"`
	EndDate        *time.Time `gorm:"column:end_date" json:"end_date"`
	Progress       *float64   `gorm:"column:progress" json:"progress"`
	AssignedTo     *string    `gorm:"column:assigned_to" json:"assigned_to"`
	Description    *string    `gorm:"column:description" json:"description"`
	Status         *string    `gorm:"column:status" json:"status"` // TODO, IN_PROGRESS, REVIEW, DONE
	Priority       *string    `gorm:"column:priority" json:"priority"`
	EstimatedHours *float64   `gorm:"column:estimated_hours" json:"estimated_hours"`
	ActualHours    *float64   `gorm:"column:actual_hours" json:"actual_hours"`
	CreatedAt      time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (ProjectTask) TableName() string { return "project_tasks" }

// ProjectMember represents a project member
type ProjectMember struct {
	ID        string    `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID  string    `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	ProjectID string    `gorm:"column:project_id;not null" json:"project_id"`
	UserID    string    `gorm:"column:user_id;type:uuid;not null" json:"user_id"`
	Role      *string   `gorm:"column:role" json:"role"` // MANAGER, MEMBER, VIEWER
	CreatedAt time.Time `gorm:"column:created_at" json:"created_at"`
}

func (ProjectMember) TableName() string { return "project_members" }

// ProjectExpense represents project expense
type ProjectExpense struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	ProjectID   string     `gorm:"column:project_id;not null" json:"project_id"`
	Description *string    `gorm:"column:description" json:"description"`
	Amount      *float64   `gorm:"column:amount" json:"amount"`
	Category    *string    `gorm:"column:category" json:"category"`
	Date        *time.Time `gorm:"column:date" json:"date"`
	CreatedAt   time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (ProjectExpense) TableName() string { return "project_expenses" }
