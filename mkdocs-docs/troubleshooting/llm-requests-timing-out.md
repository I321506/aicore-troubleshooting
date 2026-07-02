# Timeout Issues

## LLM Requests Timing Out Silently

=== "Symptoms"
    - AI Core LLM requests time out intermittently (approximately every 10–15 calls)
    - Timeouts are silent — no error messages returned
    - Response times are significantly longer than expected
    - Observed across multiple models: Claude Sonnet 4.6, Claude Haiku 4.5, GPT 5.4

=== "Possible Causes"
    - Network latency between client region (e.g., Singapore) and AI Core landscape
    - Backend service overload or resource contention
    - Intermittent connectivity issues between AI Core and upstream LLM providers

===  "Recommended Actions"
    1. Implement client-side timeout handling with appropriate retry logic
    2. Check the AI Core landscape status for any ongoing incidents
    3. Consider switching to a geographically closer AI Core landscape if available
    4. Monitor and log request durations to identify patterns
    5. Contact AI Core support with tenant ID, resource group, and timestamps of affected requests

---

## Orchestration Model Timeout and 503 Errors

??? warning "Symptoms"
    - LLM calls via Orchestration Service encounter timeout errors (600-second timeout exceeded)
    - Intermittent 503 Service Unavailable errors
    - Error: `litellm.Timeout: Connection timed out. Timeout passed=600.0`
    - Affects models like `anthropic--claude-4.6-sonnet`

??? info "Possible Causes"
    - Upstream model provider (Anthropic) experiencing capacity issues
    - Orchestration service deployment overloaded
    - Network connectivity issues between orchestration service and model backend
    - Service temporarily unavailable during maintenance or scaling events

??? tip "Recommended Actions"
    1. Implement retry logic with exponential backoff for both timeout and 503 errors
    2. Check if the orchestration deployment is healthy and running
    3. Try reducing request payload size or complexity
    4. Consider setting a shorter client-side timeout with retries rather than a single long timeout
    5. Contact AI Core support with deployment ID and timestamps of failures
