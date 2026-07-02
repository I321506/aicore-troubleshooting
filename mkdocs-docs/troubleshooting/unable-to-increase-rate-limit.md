# Unable to Increase Rate Limit (Error 100401)

!!! warning "Symptoms"
    - Rate limit increase requests fail with error code `100401` and HTTP status 400
    - Error message: `"Error occurred while calling AI API"`

!!! info "Possible Causes"
    - Insufficient permissions to modify rate limit settings
    - Rate limit configuration not yet propagated to the backend
    - Conflict with an existing pending request

!!! tip "Recommended Actions"
    1. Verify you have admin permissions on the AI Core tenant
    2. Wait and retry the request after a few minutes
    3. Cancel any pending quota increase requests before submitting a new one
    4. Contact AI Core support with the full error response and tenant ID
