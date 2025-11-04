# Python Recipe Processor

Processes PDF recipes using AI.

## Setup
```bash
    poetry install
```

## Usage
```bash
    # Run with open api
    poetry run rpr
```
```bash
    # Run with Anthropic
    poetry run rpr --anthropic
```
```bash
    # Run with Ollama
    poetry run rpr --ollama
```

## Configuration

Create a `.env` file with your API key:

```
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
OLLAMA_URL
OLLAMA_MODEL
```