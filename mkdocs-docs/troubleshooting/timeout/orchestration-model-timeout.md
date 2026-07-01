# Orchestration Model Timeout and 503 Errors

!!! warning "Symptoms"
    - LLM calls via Orchestration Service encounter timeout errors (600-second timeout exceeded)
    - Intermittent 503 Service Unavailable errors
    - Error: `litellm.Timeout: Connection timed out. Timeout passed=600.0`
    - Affects models like `anthropic--claude-4.6-sonnet`

!!! info "Possible Causes"
    - Upstream model provider (Anthropic) experiencing capacity issues
    - Orchestration service deployment overloaded
    - Network connectivity issues between orchestration service and model backend
    - Service temporarily unavailable during maintenance or scaling events

!!! tip "Recommended Actions"
    1. Implement retry logic with exponential backoff for both timeout and 503 errors
    2. Check if the orchestration deployment is healthy and running
    3. Try reducing request payload size or complexity
    4. Consider setting a shorter client-side timeout with retries rather than a single long timeout
    5. Contact AI Core support with deployment ID and timestamps of failures
