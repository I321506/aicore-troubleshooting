# Rate Limited at ~100 RPM Despite 2,000 RPM Configured Quota

!!! warning "Symptoms"
    - HTTP 429 (Too Many Requests) errors returned when exceeding ~100 requests per minute
    - AI Core quota API reports 2,000 RPM but actual throughput is capped at ~100 RPM
    - Thousands of 429 errors per hour during peak usage
    - Pending quota increase requests remain unapproved

!!! info "Possible Causes"
    - Mismatch between AI Core's reported quota and the actual underlying provider (Google Vertex AI) project-level quota
    - Backend quota not yet provisioned or synchronized with the configured limit
    - Provider-side rate limiting enforced independently of AI Core settings

!!! tip "Recommended Actions"
    1. Submit a quota increase request via the AI Core admin API or AI Launchpad
    2. Contact AI Core support to verify the actual provider-level quota allocation
    3. Implement client-side rate limiting to stay within the effective limit
    4. Use exponential backoff when receiving 429 responses
    5. Request expedited approval of pending quota increase requests with business justification
