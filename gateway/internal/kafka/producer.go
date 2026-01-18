package kafka

import (
	"context"
	"encoding/json"
	"log"
	"os"
	"strings"
	"time"

	"github.com/segmentio/kafka-go"
)

// Producer handles Kafka message publishing
type Producer struct {
	writer *kafka.Writer
}

// Event represents a generic event to be published
type Event struct {
	Type      string      `json:"type"`
	Source    string      `json:"source"`
	Timestamp time.Time   `json:"timestamp"`
	Data      interface{} `json:"data"`
	TenantID  string      `json:"tenant_id,omitempty"`
	UserID    string      `json:"user_id,omitempty"`
}

var globalProducer *Producer

// GetBrokers returns Kafka broker addresses from environment
func GetBrokers() []string {
	brokers := os.Getenv("KAFKA_BROKERS")
	if brokers == "" {
		brokers = "kafka:9092"
	}
	return strings.Split(brokers, ",")
}

// InitProducer initializes the global Kafka producer
func InitProducer() error {
	brokers := GetBrokers()

	globalProducer = &Producer{
		writer: &kafka.Writer{
			Addr:                   kafka.TCP(brokers...),
			Balancer:               &kafka.LeastBytes{},
			BatchTimeout:           10 * time.Millisecond,
			RequiredAcks:           kafka.RequireOne,
			AllowAutoTopicCreation: true,
		},
	}

	log.Printf("✓ Kafka producer initialized with brokers: %v", brokers)
	return nil
}

// CloseProducer closes the Kafka producer
func CloseProducer() error {
	if globalProducer != nil && globalProducer.writer != nil {
		return globalProducer.writer.Close()
	}
	return nil
}

// Publish sends an event to a Kafka topic
func Publish(ctx context.Context, topic string, event Event) error {
	if globalProducer == nil {
		log.Println("Warning: Kafka producer not initialized")
		return nil
	}

	event.Timestamp = time.Now()

	data, err := json.Marshal(event)
	if err != nil {
		return err
	}

	fullTopic := "mini-erp." + topic
	msg := kafka.Message{
		Topic: fullTopic,
		Key:   []byte(event.Type),
		Value: data,
	}

	if err := globalProducer.writer.WriteMessages(ctx, msg); err != nil {
		log.Printf("Failed to publish event: %v", err)
		return err
	}

	log.Printf("Event published to %s: %s", fullTopic, event.Type)
	return nil
}

// PublishAsync publishes an event asynchronously (fire and forget)
func PublishAsync(topic string, eventType string, source string, data interface{}, tenantID, userID string) {
	go func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		event := Event{
			Type:     eventType,
			Source:   source,
			Data:     data,
			TenantID: tenantID,
			UserID:   userID,
		}

		if err := Publish(ctx, topic, event); err != nil {
			log.Printf("Async publish failed for %s: %v", eventType, err)
		}
	}()
}

// PublishNotification sends a notification event
func PublishNotification(title, message, tenantID, userID, notificationType string, data map[string]interface{}) {
	event := Event{
		Type:     "notification",
		Source:   "gateway",
		TenantID: tenantID,
		UserID:   userID,
		Data: map[string]interface{}{
			"title":             title,
			"message":           message,
			"notification_type": notificationType,
			"data":              data,
		},
	}

	go func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		Publish(ctx, "notifications", event)
	}()
}
