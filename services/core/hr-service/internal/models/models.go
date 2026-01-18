package models

import (
	"time"
)

// Employee represents an employee (matches migrated DB)
type Employee struct {
	ID            string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID      string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	EmployeeCode  string     `gorm:"column:employee_code;size:20;not null" json:"employee_code"`
	FirstName     string     `gorm:"column:first_name;not null" json:"first_name"`
	LastName      string     `gorm:"column:last_name;not null" json:"last_name"`
	Email         string     `gorm:"column:email;not null" json:"email"`
	Phone         *string    `gorm:"column:phone" json:"phone"`
	Department    *string    `gorm:"column:department" json:"department"`
	JobTitle      *string    `gorm:"column:job_title" json:"job_title"`
	HireDate      *time.Time `gorm:"column:hire_date;type:date" json:"hire_date"`
	BaseSalary    *float64   `gorm:"column:base_salary" json:"base_salary"`
	Status        *string    `gorm:"column:status" json:"status"`
	NIK           *string    `gorm:"column:nik;size:20" json:"nik"`
	NPWP          *string    `gorm:"column:npwp;size:30" json:"npwp"`
	BirthDate     *time.Time `gorm:"column:birth_date;type:date" json:"birth_date"`
	BirthPlace    *string    `gorm:"column:birth_place;size:100" json:"birth_place"`
	Gender        *string    `gorm:"column:gender;size:10" json:"gender"`
	MaritalStatus *string    `gorm:"column:marital_status;size:20" json:"marital_status"`
	Religion      *string    `gorm:"column:religion;size:30" json:"religion"`
	Address       *string    `gorm:"column:address" json:"address"`
	CreatedAt     time.Time  `gorm:"column:created_at" json:"created_at"`
	UpdatedAt     time.Time  `gorm:"column:updated_at" json:"updated_at"`
}

func (Employee) TableName() string {
	return "employees"
}

// HRDepartment represents a department (matches migrated DB)
type HRDepartment struct {
	ID          string  `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string  `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Name        string  `gorm:"column:name;not null" json:"name"`
	Code        *string `gorm:"column:code" json:"code"`
	Description *string `gorm:"column:description" json:"description"`
	ManagerID   *string `gorm:"column:manager_id;type:uuid" json:"manager_id"`
	IsActive    *bool   `gorm:"column:is_active" json:"is_active"`
}

func (HRDepartment) TableName() string {
	return "hr_departments"
}

// HRPosition represents a position (matches migrated DB)
type HRPosition struct {
	ID           string  `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID     string  `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	DepartmentID *string `gorm:"column:department_id;type:uuid" json:"department_id"`
	Name         string  `gorm:"column:name;not null" json:"name"`
	Code         *string `gorm:"column:code" json:"code"`
	Description  *string `gorm:"column:description" json:"description"`
	IsActive     *bool   `gorm:"column:is_active" json:"is_active"`
}

func (HRPosition) TableName() string {
	return "hr_positions"
}

// Attendance represents an attendance record (matches migrated DB)
type Attendance struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	EmployeeID  string     `gorm:"column:employee_id;type:uuid;index;not null" json:"employee_id"`
	Date        time.Time  `gorm:"column:date;type:date;not null" json:"date"`
	CheckIn     *time.Time `gorm:"column:check_in" json:"check_in"`
	CheckOut    *time.Time `gorm:"column:check_out" json:"check_out"`
	Status      *string    `gorm:"column:status" json:"status"`
	WorkHours   *float64   `gorm:"column:work_hours" json:"work_hours"`
	OvertimeMin *int       `gorm:"column:overtime_minutes" json:"overtime_minutes"`
	LateMin     *int       `gorm:"column:late_minutes" json:"late_minutes"`
	Notes       *string    `gorm:"column:notes" json:"notes"`
	ApprovedBy  *string    `gorm:"column:approved_by;type:uuid" json:"approved_by"`
}

func (Attendance) TableName() string {
	return "attendances"
}
