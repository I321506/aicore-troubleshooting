# GenAI Hub Issues

## Deployment Not Found (404)
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

## Wrong Inference Endpoint or Request Format
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
    - For orchestration deployments, call `.../completion` with `orchestration_config` (templating and LLM module config are mandatory) — templating placeholders replace the plain messages array
    - Prefer the SAP Cloud SDK for AI (Python/JS), which resolves deployment IDs and request formats automatically

## Model Not Available in Tenant or Region
=== "Symptoms"
    - Requested model is not listed in available models
    - Deployment creation fails for a specific model
    - Specific model version unavailable
=== "Possible Causes"
    - Model not enabled/onboarded for the tenant
    - Region-specific model restrictions (availability varies by landscape)
    - Trial or free-tier account limitations (generative AI hub requires the extended service plan)
===  "Recommended Actions"
    - Verify the list of supported models for your service plan and region in SAP documentation / SAP Notes
    - Check region support and consider provisioning in a region where the model is available
    - Request model onboarding for the tenant if required
    - Use the `latest` version alias where possible to avoid version-specific unavailability

## Model Context Length Exceeded
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

## Unexpected Token Consumption Costs
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

## Orchestration Workflow Fails
=== "Symptoms"
    - Orchestration execution error returned
    - Workflow terminates before the model call is made
=== "Possible Causes"
    - Invalid module configuration in the orchestration config
    - Missing mandatory templating block (templating and LLM config are required modules)
    - Unsupported combination or ordering of orchestration modules
===  "Recommended Actions"
    - Validate the orchestration configuration against the schema
    - Verify module ordering (e.g., translation/grounding/templating sequence)
    - Ensure the templating and LLM module configuration are always present
    - Review orchestration deployment logs to identify the failing module
    - Configure orchestration fallbacks to route to an alternative model on client errors such as 429, timeouts, or when the specified model is not supported in the deployed region — each fallback entry is a complete module config, so system prompts and filter rules can differ per fallback

## Prompt Templating Errors – Placeholders Not Replaced
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

## Orchestration 400 – Unused or Unexpected Template Parameters
=== "Symptoms"
    - Error: `400 - Input Parameters: Error validating parameters. Unused parameters: ['<name>']`
    - Occurs intermittently, typically with large message histories or agent workloads with many tool definitions
    - The named "parameter" was never defined as a template variable
=== "Possible Causes"
    - Curly-brace text inside message content or tool definitions being interpreted as template placeholders by the templating module
    - Parameter validation applied across the full message history, not just the template
=== "Recommended Actions"
    - Escape or strip curly braces in user-provided content and tool schemas before sending to orchestration
    - Reduce message history size passed to the orchestration call
    - If reproducible, report it with the request ID — this behavior has been reported as an API-side validation bug
    - As a workaround, use the foundation-models (direct) endpoint for agent workloads that embed brace-heavy content

## Streaming Response Issues with Orchestration
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

## Translation Module Produces Incorrect Output
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

## Grounding Returns No Relevant Context
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

## Document Grounding Pipeline Fails for SharePoint
=== "Symptoms"
    - Pipeline creation fails or the pipeline never reaches a completed state
    - No documents indexed from the configured SharePoint site
    - Authentication errors from the pipeline against Microsoft Graph
=== "Possible Causes"
    - Misconfigured Microsoft Graph SharePoint API credentials — the most frequent setup issue; the app registration often lacks the required privileges because Microsoft administration sits with a different team
    - Generic secret for the repository created with wrong or non-base64-encoded credentials
    - Document Grounding service instance created with the wrong runtime (e.g., Cloud Foundry), producing the wrong credential type and no mTLS endpoint
    - X.509 certificate and key from the service key not extracted into separate .crt/.key files for API access
===  "Recommended Actions"
    - Verify Graph API credentials independently (query the SharePoint site directly with them) before wiring them into the pipeline
    - Recreate the generic secret with correctly base64-encoded credentials as per the grounding tutorial
    - Recreate the service instance with the correct runtime so the mTLS endpoint and certificate-based credentials are issued
    - Confirm connectivity to the Document Grounding API (url, client_id, certificates) before debugging the pipeline itself

## Documents Missing from Grounding Index
=== "Symptoms"
    - Pipeline completes but some documents are never retrievable
    - No error reported for the missing documents
=== "Possible Causes"
    - Unsupported file types — only PDF, DOCX, TXT, and MD are supported; Excel and PowerPoint files fail silently
    - `includePaths` scoping excludes the folders containing the documents
    - Documents added to the repository after the last pipeline run
===  "Recommended Actions"
    - Convert unsupported formats (XLSX, PPTX) to PDF or DOCX before indexing
    - Review `includePaths` configuration against the actual folder structure
    - Re-run or schedule the pipeline after adding new documents
    - Validate retrieval per document with a targeted query against the retrieval API

## Vector / Document Grounding API Request Errors
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
    - Treat unexplained 500s as request-format issues first: compare against a known-good request from the tutorials before raising a ticket

## Grounding Exposes Restricted Documents to All Users
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

## Legitimate Prompts Blocked by Content Filtering
=== "Symptoms"
    - HTTP 400/403 with a "content filtered" message
    - Valid business prompts rejected before reaching the model
=== "Possible Causes"
    - Overly restrictive content filtering policies (e.g., Azure Content Safety or Llama Guard thresholds set too low)
    - False positive detection on domain-specific terminology
===  "Recommended Actions"
    - Review filter severity levels in the orchestration content filtering configuration
    - Adjust safety thresholds to match the use case
    - Use exception workflows for known false-positive patterns

## Unexpected Output Blocking
=== "Symptoms"
    - Model generates output but the user receives a filtering error
=== "Possible Causes"
    - Output-side safety filter violation
===  "Recommended Actions"
    - Inspect the filtering logs to identify which category triggered the block
    - Modify prompt instructions to steer output away from flagged categories
    - Adjust output filter settings if the block is a false positive
    - Handle blocks in client code — module fallback is not triggered by content-filter hits

## Sensitive Data Not Masked
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
    - Add "masking enabled where data classification requires it" as an explicit review gate for every new orchestration config/endpoint

## Excessive Data Masking
=== "Symptoms"
    - Responses or prompts dominated by `[MASKED]` tokens
    - Business-relevant, non-sensitive terms being masked
=== "Possible Causes"
    - Overly aggressive detection rules
===  "Recommended Actions"
    - Fine-tune masking patterns and entity types
    - Review false positives and exclude safe categories
    - Use targeted masking policies per use case instead of a single global policy

## Prompt Optimization Job Fails to Start
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

## Optimized Prompt Performs Worse Than Original
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

## Prompt Optimization Produces Minimal Improvement
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

## Optimization Increases Prompt Length Excessively
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

## Optimized Prompt Causes Hallucinations
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

## Prompt Optimization Produces Inconsistent Results
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

## Optimization Job Exceeds Token Quota
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

## Evaluation Scores Contradict Human Judgment
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

## Optimized Prompt Breaks Grounding Workflow
=== "Symptoms"
    - Grounding context ignored after prompt optimization
    - Generic responses returned from a previously grounded workflow
=== "Possible Causes"
    - Optimization altered or removed the instructions and retrieved-context placeholders responsible for grounding behavior
===  "Recommended Actions"
    - Protect grounding instructions from optimization
    - Keep retrieval placeholders (e.g., `{{grounding_response}}`, `{{user_query}}`) mandatory in the template
    - Test optimized prompts with grounding datasets before promotion

## Prompt Optimization Reduces Compliance or Safety
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

## Optimization Works for One Model But Fails for Another
=== "Symptoms"
    - Optimized prompt works well with one model (e.g., GPT-4o) but performs poorly with others (e.g., Claude, Gemini)
=== "Possible Causes"
    - Different foundation models interpret instructions differently; prompt adherence varies by provider
===  "Recommended Actions"
    - Evaluate prompts per model and maintain model-specific prompt versions
    - Test across all intended production models
    - Avoid provider-specific prompt tricks in shared prompts

## Evaluation Score Too Low
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

## Evaluation Results Inconsistent
=== "Symptoms"
    - Same prompt produces different scores across evaluation runs
=== "Possible Causes"
    - Model randomness and temperature settings
    - Small evaluation dataset
===  "Recommended Actions"
    - Increase the evaluation dataset size
    - Reduce temperature for evaluation runs
    - Run multiple evaluation cycles and compare aggregate results
