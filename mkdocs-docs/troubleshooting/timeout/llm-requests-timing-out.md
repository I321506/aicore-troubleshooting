# LLM Requests Timing Out Silently

!!! warning "Symptoms"
    - AI Core LLM requests time out intermittently (approximately every 10-15 calls)
    - Timeouts are silent (no error messages returned)
    - Response times are significantly longer than expected
    - Issue observed across multiple models (Claude Sonnet 4.6, Claude Haiku 4.5, GPT 5.4)

!!! info "Possible Causes"
    - Network latency between client region (e.g., Singapore) and AI Core landscape
    - Backend service overload or resource contention
    - Intermittent connectivity issues between AI Core and upstream LLM providers

!!! tip "Recommended Actions"
    1. Implement client-side timeout handling with appropriate retry logic
    2. Check the AI Core landscape status for any ongoing incidents
    3. Consider switching to a geographically closer AI Core landscape if available
    4. Monitor and log request durations to identify patterns
    5. Contact AI Core support with tenant ID, resource group, and timestamps of affected requests
