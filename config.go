package main

type Config struct {
	Rules []Rule `json:"rules"`
}

type Rule struct {
	Name         string `json:"name"`
	Type         string `json:"type"`
	URL          string `json:"url"`
	TargetPattern string `json:"targetPattern"`
}
