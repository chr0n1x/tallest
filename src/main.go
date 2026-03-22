package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"sync"

	"github.com/chr0n1x/go-tallest/index"
)

// Parser implementations
var parsers = map[string]IndexParser{
	"zim": &index.Zim{},
}

func main() {
	configPath := os.Getenv("TALLEST_CONFIG_PATH")

	if configPath == "" {
		configPath = "./.tallest.config.json"
	}

	data, err := os.ReadFile(configPath)
	if err != nil {
		panic(err)
	}

	var config Config
	err = json.Unmarshal(data, &config)
	if err != nil {
		panic(err)
	}

	var wg sync.WaitGroup
	var mu sync.Mutex
	var failed bool

	for _, rule := range config.Rules {
		wg.Add(1)
		go func(r Rule) {
			defer wg.Done()
			fmt.Printf("Name: %s\n", r.Name)
			fmt.Printf("URL: %s\n", r.URL)
			fmt.Printf("TargetPattern: %s\n", r.TargetPattern)
			fmt.Printf("Type: %s\n", r.Type)
			fmt.Println("---")
			mu.Lock()
			if r.URL == "" {
				failed = true
			}
			mu.Unlock()
		}(rule)
	}

	wg.Wait()

	if failed {
		os.Exit(1)
	}
}
