package models

import (
	"time"
)

// User represents a user in the system (matches migrated DB)
type User struct {
	ID           string     `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	Username     string     `gorm:"column:username;size:255;uniqueIndex:ix_users_username" json:"username"`
	Email        string     `gorm:"column:email;size:255;uniqueIndex:ix_users_email;not null" json:"email"`
	PasswordHash string     `gorm:"column:password_hash;not null" json:"-"`
	Role         string     `gorm:"column:role;size:50;default:STAFF" json:"role"`
	IsVerified   bool       `gorm:"column:is_verified;default:false" json:"is_verified"`
	TenantID     *string    `gorm:"column:tenant_id;type:uuid;index" json:"tenant_id"`
	OTPCode      *string    `gorm:"column:otp_code;size:10" json:"-"`
	OTPExpiresAt *time.Time `gorm:"column:otp_expires_at" json:"-"`
	CreatedAt    time.Time  `gorm:"column:created_at;default:now()" json:"created_at"`
	UpdatedAt    time.Time  `gorm:"column:updated_at;default:now()" json:"updated_at"`
}

// TableName overrides the table name
func (User) TableName() string {
	return "users"
}

// Tenant represents a company/organization (matches migrated DB)
type Tenant struct {
	ID          string    `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	Name        string    `gorm:"column:name;size:255;not null" json:"name"`
	Slug        string    `gorm:"column:slug;size:100;uniqueIndex" json:"slug"`
	Description *string   `gorm:"column:description" json:"description"`
	IsActive    bool      `gorm:"column:is_active;default:true" json:"is_active"`
	Settings    *string   `gorm:"column:settings;type:jsonb" json:"settings"`
	CreatedAt   time.Time `gorm:"column:created_at;default:now()" json:"created_at"`
	UpdatedAt   time.Time `gorm:"column:updated_at;default:now()" json:"updated_at"`
}

func (Tenant) TableName() string {
	return "tenants"
}

// RefreshToken for JWT token refresh
type RefreshToken struct {
	ID        string    `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	UserID    string    `gorm:"column:user_id;type:uuid;index;not null" json:"user_id"`
	Token     string    `gorm:"column:token;uniqueIndex;not null" json:"-"`
	ExpiresAt time.Time `gorm:"column:expires_at" json:"expires_at"`
	CreatedAt time.Time `gorm:"column:created_at;default:now()" json:"created_at"`
	Revoked   bool      `gorm:"column:revoked;default:false" json:"revoked"`
}

func (RefreshToken) TableName() string {
	return "refresh_tokens"
}

// LoginRequest for login endpoint
type LoginRequest struct {
	Username string `json:"username" form:"username" binding:"required"`
	Password string `json:"password" form:"password" binding:"required"`
}

// RegisterRequest for registration
type RegisterRequest struct {
	Username   string `json:"username" form:"username" binding:"required,min=3,max=50"`
	Email      string `json:"email" form:"email" binding:"required,email"`
	Password   string `json:"password" form:"password" binding:"required,min=8"`
	TenantCode string `json:"tenant_code" form:"tenant_code"` // Optional: for auto-joining tenant
	Role       string `json:"role" form:"role"`               // Optional: role in tenant
}

// TokenResponse for login/refresh response
type TokenResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token,omitempty"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int64  `json:"expires_in"`
}

// UserResponse for user data
type UserResponse struct {
	ID         string  `json:"id"`
	Username   string  `json:"username"`
	Email      string  `json:"email"`
	Role       string  `json:"role"`
	IsVerified bool    `json:"is_verified"`
	TenantID   *string `json:"tenant_id"`
}

// Menu represents a menu item in the system
type Menu struct {
	ID        string  `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	Code      string  `gorm:"column:code;size:100" json:"code"`
	Label     string  `gorm:"column:label;size:255;not null" json:"label"`
	Icon      *string `gorm:"column:icon;size:100" json:"icon"`
	Path      *string `gorm:"column:path;size:255" json:"path"`
	ParentID  *string `gorm:"column:parent_id;type:uuid" json:"parent_id"`
	SortOrder int     `gorm:"column:sort_order;default:0" json:"sort_order"`
	IsActive  bool    `gorm:"column:is_active;default:true" json:"is_active"`
}

func (Menu) TableName() string { return "menus" }

// RoleMenuPermission links roles to menus per tenant
type RoleMenuPermission struct {
	ID        string `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID  string `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Role      string `gorm:"column:role;size:50;not null" json:"role"`
	MenuID    string `gorm:"column:menu_id;type:uuid;not null" json:"menu_id"`
	CanAccess bool   `gorm:"column:can_access;default:true" json:"can_access"`
}

func (RoleMenuPermission) TableName() string { return "role_menu_permissions" }

// TenantMember links users to tenants with specific roles
type TenantMember struct {
	ID        string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID  string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	UserID    string     `gorm:"column:user_id;type:uuid;index;not null" json:"user_id"`
	Role      string     `gorm:"column:role;type:memberrole;not null" json:"role"`
	InvitedBy *string    `gorm:"column:invited_by;type:uuid" json:"invited_by"`
	InvitedAt *time.Time `gorm:"column:invited_at" json:"invited_at"`
	JoinedAt  *time.Time `gorm:"column:joined_at" json:"joined_at"`
	Tenant    Tenant     `gorm:"foreignKey:TenantID" json:"tenant,omitempty"`
}

func (TenantMember) TableName() string { return "tenant_members" }

// TenantWithRole for frontend display
type TenantWithRole struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	Slug     string `json:"slug"`
	Role     string `json:"role"`
	IsActive bool   `json:"is_active"`
}

// ModuleAccess represents which modules a tenant has access to
type ModuleAccess struct {
	Module    string `json:"module"`
	HasAccess bool   `json:"has_access"`
}
