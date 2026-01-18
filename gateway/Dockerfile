# Gateway Dockerfile
FROM golang:1.23-alpine AS builder

WORKDIR /app

# Install dependencies
RUN apk add --no-cache git

# Set GOPROXY to ensure module downloads work
ENV GOPROXY=https://proxy.golang.org,direct

# Copy go mod file
COPY go.mod ./

# Initialize module and download dependencies
RUN go mod download github.com/gin-gonic/gin@v1.9.1 && \
    go mod download github.com/golang-jwt/jwt/v5@v5.2.1 && \
    go mod download github.com/redis/go-redis/v9@v9.5.1 && \
    go mod download github.com/segmentio/kafka-go@v0.4.47

# Copy source
COPY . .

# Tidy modules and generate go.sum
RUN go mod tidy

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o gateway ./cmd/main.go

# Final image
FROM alpine:latest

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /root/

COPY --from=builder /app/gateway .

EXPOSE 8000

CMD ["./gateway"]
