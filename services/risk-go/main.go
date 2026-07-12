package main

import (
	"encoding/json"
	"log"
	"math"
	"net/http"
	"os"
)

type leverageRequest struct {
	Confidence  float64 `json:"confidence"`
	MaxLeverage float64 `json:"max_leverage"`
}

type leverageResponse struct {
	Leverage float64 `json:"leverage"`
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) {
		_ = json.NewEncoder(w).Encode(map[string]bool{"ok": true})
	})
	mux.HandleFunc("/leverage", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var req leverageRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}
		confidence := math.Min(math.Max(req.Confidence, 0), 1)
		raw := 1 + ((confidence - 0.55) * 30)
		maxLev := math.Min(req.MaxLeverage, 20)
		if maxLev <= 0 {
			maxLev = 1
		}
		lev := math.Min(math.Max(raw, 1), maxLev)
		w.Header().Set("content-type", "application/json")
		_ = json.NewEncoder(w).Encode(leverageResponse{Leverage: math.Round(lev*100) / 100})
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8081"
	}
	log.Printf("risk-go listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}
