package models

import (
	"database/sql/driver"
	"fmt"
	"strings"
	"time"
)

// JSONTime is a wrapper around time.Time that handles "" as null during JSON unmarshal
type JSONTime struct {
	time.Time
}

const ctLayout = "2006-01-02T15:04:05Z07:00"

// UnmarshalJSON implements the json.Unmarshaler interface.
func (jt *JSONTime) UnmarshalJSON(b []byte) error {
	s := strings.Trim(string(b), "\"")
	if s == "null" || s == "" {
		jt.Time = time.Time{} // Zero time
		return nil
	}
	// Try primary layout (RFC3339)
	t, err := time.Parse(ctLayout, s)
	if err == nil {
		jt.Time = t
		return nil
	}

	// Try secondary layout (YYYY-MM-DD)
	t, err = time.Parse(time.DateOnly, s)
	if err == nil {
		jt.Time = t
		return nil
	}

	return err
}

// MarshalJSON implements the json.Marshaler interface.
func (jt JSONTime) MarshalJSON() ([]byte, error) {
	if jt.Time.IsZero() {
		return []byte("null"), nil
	}
	return []byte(fmt.Sprintf("\"%s\"", jt.Time.Format(ctLayout))), nil
}

// Value implements the driver.Valuer interface.
func (jt JSONTime) Value() (driver.Value, error) {
	if jt.Time.IsZero() {
		return nil, nil
	}
	return jt.Time, nil
}

// Scan implements the sql.Scanner interface.
func (jt *JSONTime) Scan(value interface{}) error {
	if value == nil {
		jt.Time = time.Time{}
		return nil
	}
	if t, ok := value.(time.Time); ok {
		jt.Time = t
		return nil
	}
	return fmt.Errorf("failed to scan JSONTime: %v", value)
}
