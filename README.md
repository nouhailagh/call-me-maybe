*This project has been created as part of the 42 curriculum by your_login.*

# Call Me Maybe - Introduction to Function Calling in LLMs

## Description
This project implements a function calling system that translates natural 
language prompts into structured function calls using a small LLM (Qwen3-0.6B) 
with constrained decoding to guarantee 100% valid JSON output.

## Instructions

### Installation
uv sync

### Run
uv run python -m src

### Custom paths
uv run python -m src
--functions_definition data/input/functions_definition.json
--input data/input/function_calling_tests.json
--output data/output/function_calling_results.json

## Algorithm Explanation
The constrained decoding works by modifying the logits at each generation step.
Only tokens that maintain valid JSON structure are allowed. Invalid tokens are 
set to negative infinity before token selection.

## Design Decisions
- Used pydantic for data validation
- Used numpy for logits manipulation
- Used Qwen3-0.6B as the default LLM model

## Performance Analysis
- Near perfect accuracy with constrained decoding
- 100% valid JSON output guaranteed
- Processes all prompts in under 5 minutes

## Challenges Faced
- Implementing constrained decoding token by token
- Handling edge cases in JSON generation
- Managing the vocabulary mapping

## Testing Strategy
- Tested with all provided prompts
- Verified JSON structure and content
- Checked function names and argument types

## Resources
- Hugging Face Transformers documentation
- Qwen3 model on Hugging Face Hub
- Pydantic documentation
- AI was used to help structure the code and debug errors