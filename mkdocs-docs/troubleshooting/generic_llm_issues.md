# Generic LLM Related Issues

## Model refuses to answer valid questions - Saftey Blocking
=== "Symptoms"
    - Safety-related response returned
    - Request blocked
    - Response blocked
=== "Possible Causes"
    - Safety filters triggered
    - Input interpreted as policy violation
    - Provider-specific moderation rules
===  "Recommended Actions"
    - Simplify and clarify prompts.
    - Remove ambiguous wording.
    - If using orchestration workflow, check content filtering configuration
    - Review provider safety guidelines.

## Model Retirement Timeline and Deprecation
=== "Symptoms"
    - Deployment not available, due to model deprecation
    - Model marked as deprecated
    - Retirement Timeline for the model is in few days/weeks. How to handle current model deployment?
=== "Possible Causes"
    - 
===  "Recommended Actions"
    - You must replace the model before the Retirement Timeline mentioned for the particular model. Anytime after the suggested replacement timeline, model will be removed from the production environments.
    - If the model is getting retired, check what is the suggested replacement model and update the deployment accordingly
    - If only model version is going to be changed and currently, you are using the version as 'latest'. No action needed.
