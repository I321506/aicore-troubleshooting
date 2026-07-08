# Onboarding and Authentication related issues


## AI Core Provisioning Failures and "Jwt issuer is not configured" Error
=== "Symptoms"
    - 504 timeout errors during AI Core service provisioning
    - "Jwt issuer is not configured" 401 error when trying to use GenAI endpoints
    - Cannot create AI Launchpad connection
    - Error appears intermittent

=== "Possible Causes"
    - Subaccount previously onboarded with a different plan (stale state)
    - Tenant warm-up period after provisioning
    - Istio/envoy configuration issues with JWT validation

===  "Recommended Actions"
    - Wait for tenant deprovisioning to complete before re-provisioning
    - Use service offboarding process before re-creating instances
    - Retry operations during warm-up period (can last several hours)
    - Try provisioning in a different region (e.g., EU20 may have less load)


## Model Deployment Creation Not Possible – Invalid Credentials
=== "Symptoms"
    - API returns `{'error': 'invalid_client', 'error_description': 'Bad credentials'}`
    - "Forbidden" error when accessing AI Launchpad after resolving auth
    - "No Ai-API Connection" error in AI Launchpad
    - "No running deployment found for model gpt-4o-mini" when attempting inference

=== "Possible Causes"
    - Using client_id/client_secret from a deprecated BTP proxy service instead of the AI Core XSUAA instance
    - Missing role collections (e.g., `ailaunchpad_connections_editor`, `genai_administrator`, `experimenter`, `manager`)
    - Browser cache issues causing "Forbidden" after role assignment
    - No deployment created for the target model

===  "Recommended Actions"
    - Create an instance of AI Launchpad in BTP and configure the AI Core service key as a new connection
    - Assign required role collections: `ailaunchpad_connections_editor`, `genai_administrator`, `experimenter`, `manager`
    - Use an incognito window after assigning roles to avoid cache issues
    - Create a configuration and then a deployment before attempting inference


## Not Able to Call Gen AI Hub API – Bad Credentials (Curl Quoting)
=== "Symptoms"
    - Auth token request returns `{"error": "invalid_client", "error_description": "Bad credentials"}`
    - AI Core service binding created with `sap-internal` plan in Kubernetes environment

=== "Possible Causes"
    - Incorrect quoting in curl request (double quotes vs single quotes)

===  "Recommended Actions"
    - Change double quotes to single quotes in the curl request for auth token retrieval


## API Access to Prompt Registry Denied on CaaS Instance
=== "Symptoms"
    - "RBAC: Access Denied" error when sending API requests to Prompt Registry
    - Same operation works on SAP AI Core instances
    - Error also seen from AI Launchpad

=== "Possible Causes"
    - Prompt Registry does not support Content-as-a-Service (CaaS) instances yet

===  "Recommended Actions"
    - Use a standard SAP AI Core instance instead of CaaS for Prompt Registry operations
    - Wait for CaaS support to be added