package main

type IndexParser interface {
	// ParseIndex returns a list of strings
	ParseIndex() []string
}