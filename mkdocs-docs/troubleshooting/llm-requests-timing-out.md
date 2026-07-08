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
    - Implement client-side timeout handling with appropriate retry logic
    - Check the AI Core landscape status for any ongoing incidents
    - Consider switching to a geographically closer AI Core landscape if available
    - Monitor and log request durations to identify patterns
    - Contact AI Core support with tenant ID, resource group, and timestamps of affected requests

## Orchestration Model Timeout and 503 Errors
===  "Symptoms"
    - LLM calls via Orchestration Service encounter timeout errors (600-second timeout exceeded)
    - Intermittent 503 Service Unavailable errors
    - Error: `litellm.Timeout: Connection timed out. Timeout passed=600.0`
    - Affects models like `anthropic--claude-4.6-sonnet`
===  "Possible Causes"
    - Upstream model provider (Anthropic) experiencing capacity issues
    - Orchestration service deployment overloaded
    - Network connectivity issues between orchestration service and model backend
    - Service temporarily unavailable during maintenance or scaling events
===  "Recommended Actions"
    - Implement retry logic with exponential backoff for both timeout and 503 errors
    - Check if the orchestration deployment is healthy and running
    - Try reducing request payload size or complexity
    - Consider setting a shorter client-side timeout with retries rather than a single long timeout
    - Contact AI Core support with deployment ID and timestamps of failures

## AI Core Deployment Timeout During Inference
===  "Symptoms"
    - Inference job takes around 8 minutes to run
    - Deployment times out before inference job completes
===  "Possible Causes"
    - Default deployment timeout is shorter than the inference processing time
    - No configurable timeout extension available
===  "Recommended Actions"
    - Contact AI Core support with tenant ID and deployment ID
    - Provide details on how long the timeout occurs
    - Inquire about options to increase deployment timeout

## Dataset API Timeouts and Empty Replies
===  "Symptoms"
    - "Read from remote host: Operation timed out"
    - "error socket hang up"
    - "Empty reply from server"
    - Both GET and PUT operations failing
===  "Possible Causes"
    - General latency issues in prod-eu landscape
    - Infrastructure issues affecting the internal production cluster
===  "Recommended Actions"
    - Monitor landscape health status
    - Raise SNOW ticket for tracking
    - Retry operations once latency issues are resolved
