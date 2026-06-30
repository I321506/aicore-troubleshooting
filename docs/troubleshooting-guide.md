# Trouble Shooting Guide


## Category: Timeout Issues

### Issue: LLM Requests Timing Out Silently

**Symptoms:**
- AI Core LLM requests time out intermittently (approximately every 10-15 calls)
- Timeouts are silent (no error messages returned)
- Response times are significantly longer than expected
- Issue observed across multiple models (Claude Sonnet 4.6, Claude Haiku 4.5, GPT 5.4)

**Possible Causes:**
- Network latency between client region (e.g., Singapore) and AI Core landscape
- Backend service overload or resource contention
- Intermittent connectivity issues between AI Core and upstream LLM providers

**Recommended Actions:**
1. Implement client-side timeout handling with appropriate retry logic
2. Check the AI Core landscape status for any ongoing incidents
3. Consider switching to a geographically closer AI Core landscape if available
4. Monitor and log request durations to identify patterns
5. Contact AI Core support with tenant ID, resource group, and timestamps of affected requests


### Issue: Orchestration Model Timeout and 503 Errors

**Symptoms:**
- LLM calls via Orchestration Service encounter timeout errors (600-second timeout exceeded)
- Intermittent 503 Service Unavailable errors
- Error: `litellm.Timeout: Connection timed out. Timeout passed=600.0`
- Affects models like `anthropic--claude-4.6-sonnet`

**Possible Causes:**
- Upstream model provider (Anthropic) experiencing capacity issues
- Orchestration service deployment overloaded
- Network connectivity issues between orchestration service and model backend
- Service temporarily unavailable during maintenance or scaling events

**Recommended Actions:**
1. Implement retry logic with exponential backoff for both timeout and 503 errors
2. Check if the orchestration deployment is healthy and running
3. Try reducing request payload size or complexity
4. Consider setting a shorter client-side timeout with retries rather than a single long timeout
5. Contact AI Core support with deployment ID and timestamps of failures


## Category: Rate Limit

### Issue: Rate Limited at ~100 RPM Despite 2,000 RPM Configured Quota

**Symptoms:**
- HTTP 429 (Too Many Requests) errors returned when exceeding ~100 requests per minute
- AI Core quota API reports 2,000 RPM but actual throughput is capped at ~100 RPM
- Thousands of 429 errors per hour during peak usage
- Pending quota increase requests remain unapproved

**Possible Causes:**
- Mismatch between AI Core's reported quota and the actual underlying provider (Google Vertex AI) project-level quota
- Backend quota not yet provisioned or synchronized with the configured limit
- Provider-side rate limiting enforced independently of AI Core settings

**Recommended Actions:**
1. Submit a quota increase request via the AI Core admin API or AI Launchpad
2. Contact AI Core support to verify the actual provider-level quota allocation
3. Implement client-side rate limiting to stay within the effective limit
4. Use exponential backoff when receiving 429 responses
5. Request expedited approval of pending quota increase requests with business justification


### Issue: Unable to Increase Rate Limit (Error 100401)

**Symptoms:**
- Rate limit increase requests fail with error code `100401` and HTTP status 400
- Error message: "Error occurred while calling AI API"
-


## Category: Rate Limit / Usage Limits

### Issue: Copilot Usage Limits Consumed Faster Under Usage-Based Billing

**Symptoms:**
- Copilot usage quota nearly exhausted after only two days despite similar usage patterns as before.
- Noticeable change in consumption rate after migration to usage-based billing model.

**Possible Causes:**
- The new usage-based billing model may count tokens/requests differently than the previous flat-rate or seat-based model.
- Background features (e.g., auto-completions, inline suggestions, chat interactions) may each consume quota separately under the new model.
- Changes in how "usage units" are defined (e.g., input + output tokens counted separately, premium model requests weighted higher).
- Possible bug or misconfiguration in the billing/metering system after the transition.

**Recommended Actions:**
- Review the usage-based billing documentation to understand exactly what counts as a "unit" of usage.
- Check the usage dashboard/breakdown to identify which activities are consuming the most quota.
- Compare the billing metrics with actual usage patterns to determine if consumption is accurately tracked.
- Report the issue to the Copilot/billing team if consumption appears disproportionate to actual usage.
- Consider adjusting usage habits (e.g., reducing inline suggestions frequency) if the billing model penalizes certain interaction types.