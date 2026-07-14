FROM golang:1.22-alpine AS build

WORKDIR /src
COPY go.mod ./
COPY main.go ./
RUN go build -o /out/risk-go .

FROM alpine:3.20
RUN adduser -D -H appuser
USER appuser
WORKDIR /app
COPY --from=build /out/risk-go /app/risk-go
CMD ["/app/risk-go"]
