package models

import "time"

// Company represents a B2B company/organization
type Company struct {
	ID        string    `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID  string    `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Name      string    `gorm:"column:name;not null" json:"name"`
	Industry  *string   `gorm:"column:industry" json:"industry"`
	Website   *string   `gorm:"column:website" json:"website"`
	Size      *string   `gorm:"column:size" json:"size"` // SMALL, MEDIUM, LARGE, ENTERPRISE
	Phone     *string   `gorm:"column:phone" json:"phone"`
	Email     *string   `gorm:"column:email" json:"email"`
	Address   *string   `gorm:"column:address" json:"address"`
	City      *string   `gorm:"column:city" json:"city"`
	Country   *string   `gorm:"column:country" json:"country"`
	TaxID     *string   `gorm:"column:tax_id" json:"tax_id"` // NPWP
	Notes     *string   `gorm:"column:notes;type:text" json:"notes"`
	IsActive  bool      `gorm:"column:is_active;default:true" json:"is_active"`
	CreatedAt time.Time `gorm:"column:created_at" json:"created_at"`
	UpdatedAt time.Time `gorm:"column:updated_at" json:"updated_at"`
	Contacts  []Contact `gorm:"foreignKey:CompanyID" json:"contacts,omitempty"`
}

func (Company) TableName() string { return "crm_companies" }

// Contact represents a contact person at a company
type Contact struct {
	ID         string    `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID   string    `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	CompanyID  *string   `gorm:"column:company_id;type:uuid;index" json:"company_id"`
	FirstName  string    `gorm:"column:first_name;not null" json:"first_name"`
	LastName   *string   `gorm:"column:last_name" json:"last_name"`
	Email      *string   `gorm:"column:email" json:"email"`
	Phone      *string   `gorm:"column:phone" json:"phone"`
	Mobile     *string   `gorm:"column:mobile" json:"mobile"`
	Position   *string   `gorm:"column:position" json:"position"` // Job Title
	Department *string   `gorm:"column:department" json:"department"`
	IsPrimary  bool      `gorm:"column:is_primary;default:false" json:"is_primary"`
	IsActive   bool      `gorm:"column:is_active;default:true" json:"is_active"`
	LinkedIn   *string   `gorm:"column:linkedin" json:"linkedin"`
	Notes      *string   `gorm:"column:notes;type:text" json:"notes"`
	CustomerID *string   `gorm:"column:customer_id;type:uuid;index" json:"customer_id"` // Link to Customer if applicable
	CreatedAt  time.Time `gorm:"column:created_at" json:"created_at"`
	UpdatedAt  time.Time `gorm:"column:updated_at" json:"updated_at"`
}

func (Contact) TableName() string { return "crm_contacts" }
