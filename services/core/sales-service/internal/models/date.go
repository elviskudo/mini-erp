package models

import (
	"database/sql/driver"
	"fmt"
	"strings"
	"time"
)

// Date is a custom type that handles date-only strings like "2026-01-20"
// as well as full RFC3339 timestamps
type Date struct {
	time.Time
}

// UnmarshalJSON handles both "2026-01-20" and "2026-01-20T00:00:00Z" formats
func (d *Date) UnmarshalJSON(b []byte) error {
	s := strings.Trim(string(b), "\"")
	if s == "" || s == "null" {
		d.Time = time.Time{}
		return nil
	}

	// Try date-only format first (most common from frontend)
	t, err := time.Parse("2006-01-02", s)
	if err == nil {
		d.Time = t
		return nil
	}

	// Try RFC3339 format
	t, err = time.Parse(time.RFC3339, s)
	if err == nil {
		d.Time = t
		return nil
	}

	// Try datetime without timezone
	t, err = time.Parse("2006-01-02T15:04:05", s)
	if err == nil {
		d.Time = t
		return nil
	}

	return fmt.Errorf("cannot parse date: %s", s)
}

// MarshalJSON outputs date in "2026-01-20" format
func (d Date) MarshalJSON() ([]byte, error) {
	if d.IsZero() {
		return []byte("null"), nil
	}
	return []byte(fmt.Sprintf("\"%s\"", d.Format("2006-01-02"))), nil
}

// Value implements driver.Valuer for database storage
func (d Date) Value() (driver.Value, error) {
	if d.IsZero() {
		return nil, nil
	}
	return d.Time, nil
}

// Scan implements sql.Scanner for database retrieval
func (d *Date) Scan(value interface{}) error {
	if value == nil {
		d.Time = time.Time{}
		return nil
	}
	switch v := value.(type) {
	case time.Time:
		d.Time = v
		return nil
	case string:
		t, err := time.Parse("2006-01-02", v)
		if err != nil {
			t, err = time.Parse(time.RFC3339, v)
		}
		if err != nil {
			return err
		}
		d.Time = t
		return nil
	default:
		return fmt.Errorf("cannot scan type %T into Date", value)
	}
}

// IsZero returns true if the date is the zero value
func (d Date) IsZero() bool {
	return d.Time.IsZero()
}
