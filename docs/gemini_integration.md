# Gemini 2.5 Flash Integration Guide

This guide explains how to work with Google's Gemini 2.5 Flash model in the Interactive Simulation System.

## Overview

The system supports Google's Gemini 2.5 models as an alternative to Groq models for generating scenarios, video prompts, and narration scripts. When configured properly, Gemini offers powerful AI capabilities with excellent performance.

## Setup

1. Ensure you have the required dependencies:
   ```bash
   pip install google-genai>=0.3.0
   ```

2. Set your Google API key in the environment:
   ```bash
   export GOOGLE_API_KEY="your_google_api_key_here"
   ```

   Alternatively, add it to your `.env` file:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

3. Run a test to verify your configuration:
   ```bash
   python test_gemini_config.py
   ```

## Key Components

### Model Configuration

The system uses `genai.types.GenerateContentConfig` to configure the Gemini model:

```python
from google.genai import types

config = types.GenerateContentConfig(
    temperature=0.6,
    top_p=0.95,
    top_k=64,
    max_output_tokens=8192,
)
```

### Thinking Capabilities (Optional)

Gemini 2.5 models support "thinking" to improve reasoning quality:

```python
thinking_config = types.ThinkingConfig(thinking_budget=1024)
config.thinking_config = thinking_config
```

The `thinking_budget` parameter (ranging from 0 to 24576) controls how many tokens the model can use for its internal thinking process.

### Model Invocation

To generate content with Gemini:

```python
response = client.models.generate_content(
    model="gemini-2.5-flash-preview-04-17",
    contents=prompt,
    config=config
)
result = response.text
```

## Fallback Mechanism

The system is designed to fall back to Groq models if:
- No Google API key is provided
- The Gemini API call fails

This ensures robustness even when Gemini is unavailable.

## Google Agent Development Kit Integration (Advanced)

For advanced agent capabilities, you can use the Google Agent Development Kit (GADK):

1. Install the GADK:
   ```bash
   pip install google-adk
   ```

2. Initialize an agent with Gemini:
   ```python
   from google.adk.agents import Agent
   
   agent = Agent(
       model="gemini-2.5-flash-preview-04-17",
       name="my_agent",
       instruction="You are a helpful AI assistant.",
   )
   ```

3. Run the agent:
   ```python
   response = agent.run("Your prompt here")
   ```

For more details, see the [Google Agent Development Kit Documentation](https://google.github.io/adk-docs/).

## Troubleshooting

### Error: "Models.generate_content() got an unexpected keyword argument 'generation_config'"

This error occurs when using the old API format. Make sure to:
1. Use `config=` instead of `generation_config=`
2. Pass a properly instantiated `GenerateContentConfig` object

### No Response or Timeout

If you experience timeouts:
1. Check your API key validity
2. Ensure you have sufficient quota
3. Consider reducing the complexity of your prompt

## Resources

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs/models/gemini)
- [Thinking Documentation](https://ai.google.dev/gemini-api/docs/thinking)
- [Agent Development Kit](https://google.github.io/adk-docs/) 