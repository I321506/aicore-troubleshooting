# Rate Limit Issues

## Rate Limited at ~100 RPM Despite 2,000 RPM Configured Quota
=== "Symptoms"
    - HTTP 429 (Too Many Requests) errors returned when exceeding ~100 requests per minute
    - AI Core quota API reports 2,000 RPM but actual throughput is capped at ~100 RPM
    - Thousands of 429 errors per hour during peak usage
    - Pending quota increase requests remain unapproved

=== "Possible Causes"
    - Mismatch between AI Core's reported quota and the actual underlying provider (Google Vertex AI) project-level quota
    - Backend quota not yet provisioned or synchronized with the configured limit
    - Provider-side rate limiting enforced independently of AI Core settings

=== "Recommended Actions"
    1. Submit a quota increase request via the AI Core admin API or AI Launchpad
    2. Contact AI Core support to verify the actual provider-level quota allocation
    3. Implement client-side rate limiting to stay within the effective limit
    4. Use exponential backoff when receiving 429 responses
    5. Request expedited approval of pending quota increase requests with business justification


## 429 TooManyRequest Error for GenAI Hub / LLM Models
=== "Symptoms"
    - Error code 429 - 'TooManyRequest' when calling models (e.g., meta--llama3.1-70b-instruct, GPT-4o)
    - All requests to GenAI hub failing with 429 errors
    - Non-stop failures lasting 45+ minutes
    - Error: "Your request has been rate limited by AI Core"

=== "Possible Causes"
    - Known infrastructure issue with the LLM hosting
    - Rate limiting at the infrastructure level
    - Traffic spike on the landscape
    - Rate limit threshold exceeded due to high concurrent usage

=== "Recommended Actions"
    - Implement retry logic with exponential backoff
    - Wait for traffic spike to subside
    - Wait for infrastructure team to resolve known issues
    - Monitor for updates from the support team


## Embedding Model Rate Limiting Triggered Prematurely
=== "Symptoms"
    - HTTP 429 Too Many Requests after only 177 requests in 45 seconds
    - Retries failing (14 retries in 15 seconds unsuccessful)
    - Previously able to create 5000 chunks but now limited to ~3000
    - Rate limit message: "Your request has been rate limited by AI Core"

=== "Possible Causes"
    - AI Core rate limiting quota set lower than expected (default ~138 RPM)
    - Global quota issue on the landscape for embedding models
    - Upstream Azure quota limitations

=== "Recommended Actions"
    - Raise a ticket to increase rate limit quota for the tenant
    - Verify current tenant quota in GitOps configuration
    - Check whether rate limit is from AI Core or upstream Azure


## Rate Limit Quota Increase Request
=== "Symptoms"
    - Rate limiting errors when exceeding default RPM limits
    - Request for 40,000 RPM denied as infeasible

=== "Possible Causes"
    - Default rate limits per tenant per model are relatively low (e.g., 78 RPM for GPT-4o)
    - Shared deployment has limits from hyperscalers (e.g., o3-mini max 5000 RPM from Azure)

=== "Recommended Actions"
    - Raise a ServiceNow ticket to request quota increase
    - Realistic increases are around 500 RPM per model per tenant
    - Implement retry logic with backoff using `x-ratelimit` response headers


## Deployment Limit of 65 Exceeded
=== "Symptoms"
    - Error: "Total number of deployments 66 exceeded the maximum limit of 65 for the tenant"

=== "Possible Causes"
    - Tenant-level deployment quota set at 65 (quota is per tenant, not per resource group)

=== "Recommended Actions"
    - Raise a SNOW (ServiceNow) request with the expected number of deployments for tracking
    - Delete existing unused deployments before creating new ones
    - Request a permanent quota increase via the incident management process


## AI Core Deployment Replicas Quota Limit Blocking Releases
=== "Symptoms"
    - Unable to scale deployments beyond 36 replicas
    - Blocking production deployments

=== "Possible Causes"
    - Replica quota limit introduced with release 2405A for tenants created after that date
    - Quota limit not widely communicated to all teams

=== "Recommended Actions"
    - Raise a request ticket to increase replica quotas for affected tenants
    - Check existing quota limits via API
    - Note: de
