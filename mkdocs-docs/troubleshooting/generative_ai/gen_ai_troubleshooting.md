# SAP AI Core Troubleshooting Guide

## Timeout Issues

### LLM Requests Timing Out Silently
=== "Symptoms"
    - AI Core LLM requests time out intermittently (approximately every 10–15 calls)
    - Timeouts are silent — no error messages returned
    - Response times are significantly longer than expected
    - Observed across multiple models
=== "Possible Causes"
    - Network latency between client region and AI Core landscape
    - Temporary service load or capacity constraints
    - Intermittent connectivity issues between AI Core and upstream model providers
    - Very large prompts or excessive grounding context inflating processing time
===  "Recommended Actions"
    - Reduce prompt size, system message length, and the number of retrieved grounding chunks
    - Check the SAP Cloud Service status page for any ongoing incidents in your region
    - Consider using a geographically closer AI Core region if available
    - Monitor and log request durations to identify patterns
    - If the issue persists, raise a support incident on component **CA-ML-AIC** with your tenant ID, resource group, and timestamps of affected requests

### Orchestration Service Timeout and 503 Errors
=== "Symptoms"
    - LLM calls via Orchestration Service encounter timeout errors (600-second timeout exceeded)
    - Intermittent 503 Service Unavailable errors
    - Error: `Connection timed out. Timeout passed=600.0`
=== "Possible Causes"
    - Upstream model provider experiencing capacity issues
    - Temporary high load on the orchestration service
    - Network connectivity issues between the orchestration service and the model backend
    - Service temporarily unavailable during maintenance or scaling events
===  "Recommended Actions"
    - Implement retry logic with exponential backoff for both timeout and 503 errors
    - Check that your orchestration deployment is healthy and in RUNNING state
    - Try reducing request payload size or complexity
    - Consider setting a shorter client-side timeout with retries rather than a single long timeout
    - Configure orchestration fallbacks so timeouts route to an alternative model configuration
    - If the issue persists, raise a support incident on component **CA-ML-AIC** with the deployment ID and timestamps of failures

### AI Core Deployment Timeout During Inference
=== "Symptoms"
    - Inference job takes several minutes to run (e.g., ~8 minutes)
    - Deployment times out before the inference job completes
=== "Possible Causes"
    - Default deployment timeout is shorter than the inference processing time
    - Timeout extension is not customer-configurable
===  "Recommended Actions"
    - Reduce the workload per request (smaller batches, less context) so processing fits within the timeout
    - Raise a support incident on component **CA-ML-AIC** with your tenant ID and deployment ID, describing when the timeout occurs, and inquire about options to increase the deployment timeout

### Dataset API Timeouts and Empty Replies
=== "Symptoms"
    - "Read from remote host: Operation timed out"
    - "error socket hang up"
    - "Empty reply from server"
    - Both GET and PUT operations failing
=== "Possible Causes"
    - Temporary latency or availability issues in the service region
===  "Recommended Actions"
    - Check the SAP Cloud Service status page for your region
    - Retry operations after a short wait — these conditions are typically transient
    - If failures persist, raise a support incident on component **CA-ML-AIC** with timestamps and affected operations

## Rate Limit Issues

### Rate Limited at ~100 RPM Despite 2,000 RPM Configured Quota
=== "Symptoms"
    - HTTP 429 (Too Many Requests) errors returned when exceeding ~100 requests per minute
    - AI Core quota API reports 2,000 RPM but actual throughput is capped at ~100 RPM
    - Thousands of 429 errors per hour during peak usage
    - Pending quota increase requests remain unapproved
=== "Possible Causes"
    - The underlying model provider (e.g., Google Vertex AI, Azure OpenAI) enforces its own capacity limits independently of the AI Core quota setting
    - The requested quota is not yet fully provisioned
    - A submitted quota increase request is still in the approval process
=== "Recommended Actions"
    - Verify the currently active quota: `GET $AI_API_URL/v2/admin/quota/model` (add the `AI-Resource-Group` header to see resource-group-level limits)
    - Submit a quota increase request via `POST $AI_API_URL/v2/admin/quota/requests` with model name, provider, new limit, and a business reason — a `requestId` is returned and the request goes through an approval process
    - Check the status of pending requests via `GET $AI_API_URL/v2/admin/quota/requests`; to follow up, raise a support incident on component **CA-ML-AIC** referencing the requestId
    - Implement client-side rate limiting to stay within the effective limit
    - Use exponential backoff with jitter when receiving 429 responses

### 429 TooManyRequest Error for GenAI Hub / LLM Models
=== "Symptoms"
    - Error code 429 - 'TooManyRequest' when calling models (e.g., meta--llama3.1-70b-instruct, GPT-4o)
    - All requests to GenAI hub failing with 429 errors
    - Sustained failures lasting 45+ minutes
    - Error: "Your request has been rate limited by AI Core"
=== "Possible Causes"
    - Tenant-level rate limit exceeded — limits are model-specific, measured in RPM, shared by all resource groups by default, shared across all versions of a model, and reset every minute
    - Resource-group-level rate limit exceeded (if a dedicated limit is configured for that resource group)
    - Model provider capacity exceeded — hyperscalers can reject requests independently of AI Core quotas
    - Temporary backend saturation — a 429 does not always mean a rate limit is exceeded
=== "Recommended Actions"
    - Check the rate limit response headers before implementing retry logic: `Retry-After` (seconds to wait), `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` (Unix timestamp) — verify the headers are present first
    - Implement retry with exponential backoff and jitter: wait an initial interval (e.g., 1s), honor `Retry-After` if present, increase the wait exponentially after each failed retry, and cap retries (e.g., 5 attempts or 60s total) — never retry immediately
    - Prefer the SAP-provided SDKs, which offer configurable retry behavior, over calling the APIs directly
    - Spread requests evenly over time instead of sending bursts; cache responses for repeated prompts
    - Use model fallbacks — the orchestration service supports fallback configurations that route to an alternative model on 429
    - Isolate workloads by assigning different applications to separate resource groups with their own limits to prevent shared quota exhaustion
    - If sustained failures continue despite backoff, raise a support incident on component **CA-ML-AIC**

### Embedding Model Rate Limiting Triggered Prematurely
=== "Symptoms"
    - HTTP 429 Too Many Requests after only 177 requests in 45 seconds
    - Retries failing (e.g., 14 retries in 15 seconds unsuccessful)
    - Previously able to process larger workloads than currently possible
    - Rate limit message: "Your request has been rate limited by AI Core"
=== "Possible Causes"
    - The default rate limit for the embedding model is lower than assumed
    - Rapid retries without backoff consuming the per-minute window (limits reset every minute)
    - Model provider quota limitations enforced independently of AI Core
=== "Recommended Actions"
    - Verify the current effective limit for the embedding model: `GET $AI_API_URL/v2/admin/quota/model`
    - Inspect the `Retry-After` and `X-RateLimit-*` response headers to understand the active limit and reset window
    - Replace rapid retries with exponential backoff and jitter; many retries within the same minute window will always fail
    - Submit a quota increase request via `POST $AI_API_URL/v2/admin/quota/requests` with business justification

### Rate Limit Quota Increase Request
=== "Symptoms"
    - Rate limiting errors when exceeding default RPM limits
    - Very large increase requests (e.g., 40,000 RPM) denied as infeasible
=== "Possible Causes"
    - Default rate limits per tenant per model are relatively low (e.g., 78 RPM for GPT-class models)
    - Models run on shared capacity with upper limits set by the model providers
    - Requested limit exceeds what the underlying provider capacity can support
=== "Recommended Actions"
    - Check current limits first: `GET $AI_API_URL/v2/admin/quota/model` returns per-model limits with `unit: requestPerMinute`
    - Submit a tenant-level increase: `POST $AI_API_URL/v2/admin/quota/requests` with `resourceType: model`, the target `modelName`/`providerName`, the new limit, and a `reason`
    - For a resource-group-scoped limit, include the `AI-Resource-Group` header and `"scope": "resource_group"` in the request body
    - Track approval via `GET $AI_API_URL/v2/admin/quota/requests`; follow up with a support incident on component **CA-ML-AIC** if needed
    - Keep requested limits realistic; moderate increases (e.g., ~500 RPM per model per tenant) are more likely to be approved than very large ones
    - Implement retry logic with backoff using the `X-RateLimit` response headers in parallel

### Deployment Limit Exceeded
=== "Symptoms"
    - Error: "Total number of deployments X exceeded the maximum limit of Y for the tenant"
=== "Possible Causes"
    - The tenant-level deployment quota has been reached (the quota applies per tenant, not per resource group)
=== "Recommended Actions"
    - Delete existing unused deployments before creating new ones
    - Raise a support incident on component **CA-ML-AIC** stating the number of deployments you require and the business justification to request a quota increase

### AI Core Deployment Replicas Quota Limit Blocking Releases
=== "Symptoms"
    - Unable to scale deployments beyond the replica limit (e.g., 36 replicas)
    - Blocking production deployments
=== "Possible Causes"
    - A tenant-level replica quota applies to deployments
=== "Recommended Actions"
    - Check your current quota limits via the quota API
    - Raise a support incident on component **CA-ML-AIC** to request a replica quota increase for the affected tenant, including the target replica count and business justification

## Onboarding and Authentication Issues

### AI Core Provisioning Failures and "Jwt issuer is not configured" Error
=== "Symptoms"
    - 504 timeout errors during AI Core service provisioning
    - "Jwt issuer is not configured" 401 error when trying to use GenAI endpoints
    - Cannot create AI Launchpad connection
    - Error appears intermittent
=== "Possible Causes"
    - Subaccount previously onboarded with a different service plan (residual state from the earlier setup)
    - Tenant warm-up period after provisioning — the service can take time to become fully operational
    - Temporary platform-side configuration delay in token validation for a newly provisioned tenant
===  "Recommended Actions"
    - If re-provisioning, first delete the existing instance and wait for offboarding to complete before creating a new one
    - Retry operations during the warm-up period (this can last several hours after provisioning)
    - Try provisioning in a different region if the issue persists
    - If the error continues beyond the warm-up period, raise a support incident on component **CA-ML-AIC**

### Model Deployment Creation Not Possible – Invalid Credentials
=== "Symptoms"
    - API returns `{'error': 'invalid_client', 'error_description': 'Bad credentials'}`
    - "Forbidden" error when accessing AI Launchpad after resolving auth
    - "No Ai-API Connection" error in AI Launchpad
    - "No running deployment found for model gpt-4o-mini" when attempting inference
=== "Possible Causes"
    - Using client_id/client_secret from an old or different service instance instead of the current AI Core instance's service key
    - Missing role collections (e.g., `ailaunchpad_connections_editor`, `genai_administrator`, `experimenter`, `manager`)
    - Browser cache issues causing "Forbidden" after role assignment
    - No deployment created for the target model
===  "Recommended Actions"
    - Create a fresh service key on the current AI Core instance and configure it as a new connection in AI Launchpad
    - Assign the required role collections: `ailaunchpad_connections_editor`, `genai_administrator`, `experimenter`, `manager`
    - Use an incognito window after assigning roles to avoid cache issues
    - Create a configuration and then a deployment before attempting inference

### Not Able to Call Gen AI Hub API – Bad Credentials
=== "Symptoms"
    - Auth token request returns `{"error": "invalid_client", "error_description": "Bad credentials"}`
=== "Possible Causes"
    - Incorrect quoting in the curl request (double quotes vs single quotes causing shell interpretation of special characters)
    - `/oauth/token` suffix missing from the auth URL (the service key `url` field does not include it)
    - Credentials mangled on copy-paste — client IDs contain special characters like `!` and `|`
===  "Recommended Actions"
    - Use single quotes around credentials in curl requests so the shell does not interpret special characters
    - Append `/oauth/token` to the `url` value from the service key when requesting tokens
    - Re-paste `clientid`/`clientsecret` carefully and check for trailing whitespace

### Authentication Token Expiry During Long-Running Operations
=== "Symptoms"
    - 401 Unauthorized errors after a period of successful API calls
    - Long-running batch jobs or pipelines failing partway through
=== "Possible Causes"
    - OAuth bearer tokens have a limited lifetime and expire mid-operation
    - Token cached at application start and never refreshed
    - Missing or malformed `Bearer ` prefix in the Authorization header
===  "Recommended Actions"
    - Implement proactive token refresh before expiry rather than reacting to 401s
    - Use the SAP-provided SDKs, which handle the token lifecycle automatically
    - On 401, refresh the token once and retry before failing the operation
    - Verify the Authorization header format: `Authorization: Bearer <token>`

### API Access to Prompt Registry Denied on CaaS Instance
=== "Symptoms"
    - "RBAC: Access Denied" error when sending API requests to Prompt Registry
    - Same operation works on SAP AI Core instances
    - Error also seen from AI Launchpad
=== "Possible Causes"
    - Prompt Registry does not currently support Content-as-a-Service (CaaS) instances
===  "Recommended Actions"
    - Use a standard SAP AI Core instance instead of CaaS for Prompt Registry operations
    - Check SAP release notes for when CaaS support becomes available

## Generic LLM Issues

### Model Refuses to Answer Valid Questions – Safety Blocking
=== "Symptoms"
    - Safety-related response returned
    - Request blocked
    - Response blocked
=== "Possible Causes"
    - Safety filters triggered
    - Input interpreted as policy violation
    - Provider-specific moderation rules
===  "Recommended Actions"
    - Simplify and clarify prompts
    - Remove ambiguous wording
    - If using an orchestration workflow, check the content filtering configuration
    - Review the model provider's safety guidelines

### Model Retirement Timeline and Deprecation
=== "Symptoms"
    - Deployment not available due to model deprecation
    - Model marked as deprecated
    - Retirement timeline for the model is in a few days/weeks — how to handle the current model deployment?
=== "Possible Causes"
    - Model versions have deprecation dates; deployments pinned to a specific version stop working on that date
===  "Recommended Actions"
    - Replace the model before the retirement timeline; after the deadline, the model is removed from production environments
    - Check the suggested replacement model in the SAP documentation and update the deployment accordingly
    - If only the model version is changing and you are using version `latest`, no action is needed

## GenAI Hub Issues

### Deployment Not Found (404)
=== "Symptoms"
    - API returns `{"error":{"code":"404","message":"Resource not found"}}`
    - Inference calls fail even though the deployment shows RUNNING in AI Launchpad
=== "Possible Causes"
    - Incorrect deployment ID in the request URL
    - Missing or incorrect `AI-Resource-Group` header
    - Two AI Core instances in the subaccount — the service key used for the token belongs to a different instance than the one owning the deployment
    - Deployment exists in a different resource group
    - Deployment was deleted or is no longer in RUNNING state
===  "Recommended Actions"
    - Verify the deployment ID against the deployments list API or AI Launchpad
    - Verify the `AI-Resource-Group` header matches the resource group that owns the deployment
    - If multiple AI Core instances exist, create and use a service key from the instance that owns the resource group containing the deployment
    - Check the deployment status in AI Launchpad and recreate it if it is stopped or deleted

### Wrong Inference Endpoint or Request Format
=== "Symptoms"
    - 404 or 400 errors even though the deployment ID, token, and resource group are correct
    - OpenAI-style request body rejected by an orchestration deployment (or vice versa)
    - AI Launchpad shows configurations but inference calls fail
=== "Possible Causes"
    - Mixing up the two deployment types: foundation-models deployments expose an OpenAI-compatible `/chat/completions` endpoint, while orchestration deployments expose `/completion` and require an `orchestration_config` with `module_configurations` and a `template`
    - Configuration created under the wrong scenario (`orchestration` instead of `foundation-models`, or vice versa) for the intended consumption pattern
    - Model-specific endpoint suffix wrong (e.g., embeddings vs. chat vs. `/predict` for SAP-RPT models)
===  "Recommended Actions"
    - Check which scenario the deployment's configuration belongs to before choosing the request format
    - For direct model access, create the configuration with scenario `foundation-models` and call `.../v2/inference/deployments/<id>/chat/completions` with an OpenAI-compatible body
    - For orchestration deployments, call `.../completion` with `orchestration_config` (templating and LLM module config are mandatory)
    - Prefer the SAP Cloud SDK for AI (Python/JS), which resolves deployment IDs and request formats automatically

### Model Not Available in Tenant or Region
=== "Symptoms"
    - Requested model is not listed in available models
    - Deployment creation fails for a specific model
    - Specific model version unavailable
=== "Possible Causes"
    - Model not available for the tenant's service plan
    - Region-specific model restrictions (availability varies by region)
    - Trial or free-tier account limitations (generative AI hub requires the extended service plan)
===  "Recommended Actions"
    - Verify the list of supported models for your service plan and region in the SAP documentation / SAP Notes
    - Check region support and consider provisioning in a region where the model is available
    - Use the `latest` version alias where possible to avoid version-specific unavailability

### Model Context Length Exceeded
=== "Symptoms"
    - 400 error indicating the prompt exceeds the model's maximum context length
    - Requests fail only for long conversations or grounding-heavy prompts, while short prompts work
    - Truncated or cut-off responses when `max_tokens` plus prompt size approaches the model limit
=== "Possible Causes"
    - Large message history accumulated over multi-turn conversations
    - Excessive grounding context injected into the prompt by the retrieval module
    - `max_tokens` set too high relative to the remaining context window
    - Model switched to a variant with a smaller context window
===  "Recommended Actions"
    - Trim or summarize message history before sending; keep only the turns needed for the task
    - Reduce the number and size of retrieved grounding chunks
    - Lower `max_tokens` or move to a model variant with a larger context window
    - Log token counts per request (prompt vs. completion) to identify what is consuming the window

### Unexpected Token Consumption Costs
=== "Symptoms"
    - High token consumption in metering reports
    - Budget overrun without a corresponding increase in traffic
=== "Possible Causes"
    - Large prompts or large system messages sent with every request
    - Excessive grounding context retrieved and injected into prompts
    - Evaluation or prompt optimization jobs consuming tokens in the background
    - Grounding modules metered separately (vector storage size, text blocks, API calls each convert to capacity units)
===  "Recommended Actions"
    - Monitor token usage regularly with GenAI Hub token metering
    - Track consumption per application/resource group to identify the source
    - Reduce prompt and system message size; limit the number of retrieved grounding chunks
    - Use smaller/cheaper models where the use case allows
    - Review grounding storage: remove obsolete collections and documents that accrue storage costs

### Orchestration Workflow Fails
=== "Symptoms"
    - Orchestration execution error returned
    - Workflow terminates before the model call is made
=== "Possible Causes"
    - Invalid module configuration in the orchestration config
    - Missing mandatory templating block (templating and LLM config are required modules)
    - Unsupported combination or ordering of orchestration modules
===  "Recommended Actions"
    - Validate the orchestration configuration against the documented schema
    - Verify module ordering (e.g., translation/grounding/templating sequence)
    - Ensure the templating and LLM module configuration are always present
    - Review the orchestration deployment logs in AI Launchpad to identify the failing module
    - Configure orchestration fallbacks to route to an alternative model on client errors such as 429, timeouts, or when the specified model is not supported in the deployed region — each fallback entry is a complete module config, so system prompts and filter rules can differ per fallback

### Prompt Templating Errors – Placeholders Not Replaced
=== "Symptoms"
    - Placeholders appear unresolved in the final prompt (e.g., `Hello {{customer_name}}`)
    - Template variables visible in model responses
=== "Possible Causes"
    - Missing input parameters at inference time
    - Incorrect template syntax
    - Parameter name mismatch between template and request payload
===  "Recommended Actions"
    - Validate that all template parameters are supplied in the request
    - Add input validation before invoking the orchestration service
    - Define default values for optional placeholders
    - Test the template independently before wiring it into the workflow

### Orchestration 400 – Unused or Unexpected Template Parameters
=== "Symptoms"
    - Error: `400 - Input Parameters: Error validating parameters. Unused parameters: ['<name>']`
    - Occurs intermittently, typically with large message histories or agent workloads with many tool definitions
    - The named "parameter" was never defined as a template variable
=== "Possible Causes"
    - Curly-brace text inside message content or tool definitions being interpreted as template placeholders by the templating module
    - Parameter validation applied across the full message history, not just the template
=== "Recommended Actions"
    - Escape or strip curly braces in user-provided content and tool schemas before sending to orchestration
    - Reduce the message history size passed to the orchestration call
    - If reproducible, raise a support incident on component **CA-ML-AIC** including the request ID from the error
    - As a workaround, use the foundation-models (direct) endpoint for agent workloads that embed brace-heavy content

### Streaming Response Issues with Orchestration
=== "Symptoms"
    - Streaming requests fail while identical non-streaming requests succeed
    - Expected model fallback does not happen mid-stream
    - Stream terminates without a fallback after a content filter triggers
=== "Possible Causes"
    - For streaming requests, fallback only happens before the stream starts — the orchestration service never switches models mid-stream
    - Module fallback is not triggered by content-filter hits or invalid-input errors, only by availability/errors of the model itself
    - Client or intermediate proxy not handling server-sent events correctly
===  "Recommended Actions"
    - Design fallback expectations accordingly: test fallback with non-streaming calls first, then verify streaming behavior separately
    - Handle content-filter blocks in client code — do not rely on fallback to recover from them
    - Include streaming settings in the orchestration config spec when using stored configurations from the Prompt Registry
    - Verify the client consumes SSE properly (no buffering proxies, correct `Accept` handling)

### Translation Module Produces Incorrect Output
=== "Symptoms"
    - Response returned in the wrong language
    - Mixed-language responses
=== "Possible Causes"
    - Unsupported source/target language pair
    - Ambiguous source language when auto-detection is used
    - Translation placed at the wrong position in the workflow (e.g., after grounding)
===  "Recommended Actions"
    - Explicitly define source and target languages instead of relying on auto-detection
    - Validate text encoding of the input
    - Test the workflow module ordering and move translation before/after the appropriate step

### Grounding Returns No Relevant Context
=== "Symptoms"
    - Generic answers with no enterprise-specific content
    - Hallucinated responses
    - Empty grounding context in orchestration results
=== "Possible Causes"
    - Missing embeddings or failed data ingestion
    - Incorrect vector search configuration
    - Document repository misconfiguration
    - Wrong repository ID or filters in the grounding request configuration
===  "Recommended Actions"
    - Verify ingestion pipelines completed successfully (check pipeline status via the Pipelines API)
    - Rebuild embeddings for the affected repository
    - Verify the vector index and search configuration, and that the repository ID in the orchestration grounding config matches the indexed repository
    - Test retrieval independently (query the retrieval API directly) before testing end-to-end

### Document Grounding Pipeline Fails for SharePoint
=== "Symptoms"
    - Pipeline creation fails or the pipeline never reaches a completed state
    - No documents indexed from the configured SharePoint site
    - Authentication errors from the pipeline against Microsoft Graph
=== "Possible Causes"
    - Misconfigured Microsoft Graph SharePoint API credentials — the app registration often lacks the required privileges, especially when Microsoft administration is handled by a different team
    - Generic secret for the repository created with wrong or non-base64-encoded credentials
    - Document Grounding service instance created with the wrong runtime option, producing the wrong credential type and no mTLS endpoint
    - X.509 certificate and key from the service key not extracted into separate .crt/.key files for API access
===  "Recommended Actions"
    - Verify Graph API credentials independently (query the SharePoint site directly with them) before wiring them into the pipeline
    - Recreate the generic secret with correctly base64-encoded credentials as described in the grounding documentation
    - Recreate the service instance with the correct runtime so the mTLS endpoint and certificate-based credentials are issued
    - Confirm connectivity to the Document Grounding API (url, client_id, certificates) before debugging the pipeline itself

### Documents Missing from Grounding Index
=== "Symptoms"
    - Pipeline completes but some documents are never retrievable
    - No error reported for the missing documents
=== "Possible Causes"
    - Unsupported file types — only PDF, DOCX, TXT, and MD are supported; unsupported formats such as Excel and PowerPoint are skipped without an error
    - `includePaths` scoping excludes the folders containing the documents
    - Documents added to the repository after the last pipeline run
===  "Recommended Actions"
    - Convert unsupported formats (XLSX, PPTX) to PDF or DOCX before indexing
    - Review the `includePaths` configuration against the actual folder structure
    - Re-run or schedule the pipeline after adding new documents
    - Validate retrieval per document with a targeted query against the retrieval API

### Vector / Document Grounding API Request Errors
=== "Symptoms"
    - "Internal server error" (500) when creating collections or pipelines
    - 400 errors on retrieval/search requests
=== "Possible Causes"
    - Missing `Content-Type: application/json` header — known to surface as a misleading 500 on collection/pipeline creation
    - Missing `dataRepositoryType: "vector"` field in retrieval request filters — returns a 400
    - Missing `AI-Resource-Group` header, or resource group not enabled for grounding
===  "Recommended Actions"
    - Always send `Content-Type: application/json` on grounding API POST requests
    - Include `"dataRepositoryType": "vector"` in retrieval filters
    - Verify the resource group has grounding enabled and is passed in the `AI-Resource-Group` header
    - Treat unexplained 500s as request-format issues first: compare against a known-good request from the SAP tutorials before raising a support incident

### Grounding Exposes Restricted Documents to All Users
=== "Symptoms"
    - Users receive answers containing content from documents they cannot access in the source repository
    - Compliance/security review flags the grounding setup
=== "Possible Causes"
    - The pipeline indexes documents with a system-level service account into a shared vector store; retrieval does not check the individual user's SharePoint permissions
=== "Recommended Actions"
    - Treat everything indexed as visible to every user of the assistant — index only content approved for the full audience
    - Use `includePaths` to restrict indexing to folders where every document is appropriate for every user
    - Consider a dedicated repository/site containing only approved content
    - For differing permission levels, separate use cases into different resource groups/pipelines with separate consuming applications

### Hallucinations Despite Grounding
=== "Symptoms"
    - Model fabricates information even when documents are retrieved
    - Retrieved documents appear to be ignored
=== "Possible Causes"
    - Poor retrieval quality or low similarity scores
    - Insufficient context passed to the model
    - Prompt does not instruct the model to answer only from context
===  "Recommended Actions"
    - Improve the chunking strategy and increase retrieval relevance
    - Add a context-enforcement instruction to the prompt, e.g. answer only from the supplied context and respond "I don't know" when the answer is unavailable
    - Keep the retrieved context placeholder (e.g., `{{grounding_response}}`) mandatory in the template

### Grounding Performance Degradation
=== "Symptoms"
    - Long orchestration runtime for grounding-enabled workflows
=== "Possible Causes"
    - Very large document repositories
    - Excessive number of document chunks retrieved
    - Inefficient indexing strategy
===  "Recommended Actions"
    - Optimize chunk sizes and reduce the number of retrieved chunks
    - Remove obsolete documents from repositories
    - Filter repositories so only relevant collections are searched

### Legitimate Prompts Blocked by Content Filtering
=== "Symptoms"
    - HTTP 400/403 with a "content filtered" message
    - Valid business prompts rejected before reaching the model
=== "Possible Causes"
    - Overly restrictive content filtering thresholds in the orchestration configuration
    - False positive detection on domain-specific terminology
===  "Recommended Actions"
    - Review filter severity levels in the orchestration content filtering configuration
    - Adjust safety thresholds to match the use case
    - Use exception workflows for known false-positive patterns

### Unexpected Output Blocking
=== "Symptoms"
    - Model generates output but the user receives a filtering error
=== "Possible Causes"
    - Output-side safety filter violation
===  "Recommended Actions"
    - Identify which filter category triggered the block from the response details
    - Modify prompt instructions to steer output away from flagged categories
    - Adjust output filter settings if the block is a false positive
    - Handle blocks in client code — module fallback is not triggered by content-filter hits

### Sensitive Data Not Masked
=== "Symptoms"
    - PII visible in prompts sent to the model provider
=== "Possible Causes"
    - Data masking policy misconfiguration
    - Data pattern not supported by the default masking entities
    - Masking is opt-in per orchestration configuration — a copied config without the masking module sends raw data
===  "Recommended Actions"
    - Validate the masking rules configured in the orchestration workflow
    - Add custom patterns for domain-specific identifiers
    - Test the masking configuration with known PII samples before go-live
    - Add "masking enabled where data classification requires it" as an explicit review gate for every new orchestration configuration

### Excessive Data Masking
=== "Symptoms"
    - Responses or prompts dominated by `[MASKED]` tokens
    - Business-relevant, non-sensitive terms being masked
=== "Possible Causes"
    - Overly aggressive detection rules
===  "Recommended Actions"
    - Fine-tune masking patterns and entity types
    - Review false positives and exclude safe categories
    - Use targeted masking policies per use case instead of a single global policy

### Prompt Optimization Job Fails to Start
=== "Symptoms"
    - Optimization job remains in Pending state or terminates immediately
    - API returns validation errors
    - No optimized prompt generated
=== "Possible Causes"
    - Invalid dataset format or missing mandatory fields in the evaluation dataset
    - Incorrect optimization configuration
    - Unsupported model selected for the optimization workflow
    - Resource group access issues
===  "Recommended Actions"
    - Validate the dataset structure and required input/output columns before submission
    - Check resource group permissions
    - Confirm the selected model supports the optimization workflow
    - Review the optimization execution logs for validation details

### Optimized Prompt Performs Worse Than Original
=== "Symptoms"
    - Lower evaluation scores and reduced response accuracy after optimization
    - More hallucinations; users prefer the original prompt
=== "Possible Causes"
    - Dataset bias – optimization dataset does not represent production traffic
    - Overfitting – optimizer learns specific examples rather than general behavior
    - Small dataset size or poor/inconsistent ground truth labels
===  "Recommended Actions"
    - Use representative datasets covering diverse business scenarios
    - Increase evaluation sample size and keep separate training/validation datasets
    - Always benchmark the optimized prompt against the original and perform A/B testing before production rollout
    - Keep the original prompt version for rollback

### Prompt Optimization Produces Minimal Improvement
=== "Symptoms"
    - Evaluation score improvement less than ~5%
    - Generated prompt nearly identical to the original
=== "Possible Causes"
    - Original prompt is already near-optimal
    - Low quality examples that do not challenge the model
    - Weak or misaligned evaluation criteria
===  "Recommended Actions"
    - Review optimization goals and strengthen evaluation datasets
    - Add edge cases and complex examples
    - Define measurable evaluation criteria (accuracy, groundedness, completeness, toxicity reduction, conciseness)

### Optimization Increases Prompt Length Excessively
=== "Symptoms"
    - A one-line prompt becomes several paragraphs of instructions after optimization
    - Increased latency, cost, and token consumption per request
=== "Possible Causes"
    - Optimizer maximizes quality without considering token cost
    - Optimization focused solely on the evaluation score
===  "Recommended Actions"
    - Define prompt length constraints for the optimization job
    - Monitor and compare token cost before deployment
    - Balance quality against latency, throughput, and context window limits

### Optimized Prompt Causes Hallucinations
=== "Symptoms"
    - Model fabricates information after optimization
    - Confidence increases despite incorrect answers
=== "Possible Causes"
    - Optimization removed explicit grounding constraints from the prompt
    - Evaluation dataset does not penalize hallucinations (optimizer prioritizes completeness)
    - Weak retrieval context
===  "Recommended Actions"
    - Always retain context-enforcement constraints in the prompt (answer only from provided context; say "I don't know" otherwise)
    - Include hallucination-focused evaluation metrics and measure groundedness separately
    - Validate optimized prompts against real business documents

### Prompt Optimization Produces Inconsistent Results
=== "Symptoms"
    - The same optimization run multiple times produces different prompts
    - Scores vary across runs and across teams
=== "Possible Causes"
    - LLM non-determinism (optimization itself uses foundation models)
    - Variable temperature settings between runs
    - Small dataset amplifying variations
    - Dataset, model version, or evaluation criteria changed between runs
===  "Recommended Actions"
    - Use larger evaluation datasets and execute multiple optimization runs, comparing results statistically
    - Freeze evaluation datasets and track model versions and optimization parameters
    - Store prompt versions with their evaluation scores; never overwrite production prompts without version control
    - Maintain an optimization audit history for reproducibility

### Optimization Job Exceeds Token Quota
=== "Symptoms"
    - 429 errors during optimization
    - Optimization stops midway
    - Excessive token consumption from optimization traffic
=== "Possible Causes"
    - Large datasets and multiple optimization iterations
    - Long prompts and large reference outputs
    - Optimization traffic sharing the same model-specific RPM quota as production workloads (all resource groups share the tenant limit by default)
===  "Recommended Actions"
    - Check the effective model rate limit consumed by optimization runs: `GET $AI_API_URL/v2/admin/quota/model`
    - Use sampling techniques and start with smaller datasets
    - Remove unnecessary examples and split optimization into batches
    - Monitor token usage frequently during the job; honor `Retry-After` headers on 429s during optimization
    - Run optimization jobs in a dedicated resource group with its own rate limit to avoid exhausting the quota shared with production traffic

### Evaluation Scores Contradict Human Judgment
=== "Symptoms"
    - High automated evaluation score (e.g., 92%) but poor business-user ratings
=== "Possible Causes"
    - Metric misalignment – optimization objective differs from the business objective
    - Evaluation rubric focuses on syntax rather than business accuracy
    - Optimization examples lack enterprise/domain context
===  "Recommended Actions"
    - Include SME-reviewed benchmark datasets
    - Combine automated and human evaluation
    - Create domain-specific evaluation metrics (policy compliance, business process correctness, regulatory accuracy, extraction accuracy)

### Optimized Prompt Breaks Grounding Workflow
=== "Symptoms"
    - Grounding context ignored after prompt optimization
    - Generic responses returned from a previously grounded workflow
=== "Possible Causes"
    - Optimization altered or removed the instructions and retrieved-context placeholders responsible for grounding behavior
===  "Recommended Actions"
    - Protect grounding instructions from optimization
    - Keep retrieval placeholders (e.g., `{{grounding_response}}`, `{{user_query}}`) mandatory in the template
    - Test optimized prompts with grounding datasets before promotion

### Prompt Optimization Reduces Compliance or Safety
=== "Symptoms"
    - More unsafe outputs and increased policy violations after optimization
    - Content filtering triggers more frequently
=== "Possible Causes"
    - Optimizer removed safety instructions while focusing on answer quality
    - Evaluation dataset lacks toxicity/compliance scenarios
===  "Recommended Actions"
    - Include safety-related test cases and compliance metrics in evaluation
    - Test optimized prompts with content filtering enabled after every optimization run
    - Review prompt modifications manually before promotion

### Optimization Works for One Model But Fails for Another
=== "Symptoms"
    - Optimized prompt works well with one model (e.g., GPT-4o) but performs poorly with others (e.g., Claude, Gemini)
=== "Possible Causes"
    - Different foundation models interpret instructions differently; prompt adherence varies by provider
===  "Recommended Actions"
    - Evaluate prompts per model and maintain model-specific prompt versions
    - Test across all intended production models
    - Avoid provider-specific prompt tricks in shared prompts

### Evaluation Score Too Low
=== "Symptoms"
    - Accuracy below expectation
    - Failing benchmarks
=== "Possible Causes"
    - Poor prompts or weak grounding
    - Wrong model selection for the task
===  "Recommended Actions"
    - Review failed examples individually to find failure patterns
    - Improve retrieval quality
    - Test alternative models for the use case

### Evaluation Results Inconsistent
=== "Symptoms"
    - Same prompt produces different scores across evaluation runs
=== "Possible Causes"
    - Model randomness and temperature settings
    - Small evaluation dataset
===  "Recommended Actions"
    - Increase the evaluation dataset size
    - Reduce temperature for evaluation runs
    - Run multiple evaluation cycles and compare aggregate results
