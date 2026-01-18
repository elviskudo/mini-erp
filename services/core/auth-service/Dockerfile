FROM golang:1.23-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git

ENV GOPROXY=https://proxy.golang.org,direct

COPY go.mod ./
RUN go mod download

COPY . .
RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o auth-service ./cmd/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates tzdata
WORKDIR /root/
COPY --from=builder /app/auth-service .
EXPOSE 8010
CMD ["./auth-service"]
