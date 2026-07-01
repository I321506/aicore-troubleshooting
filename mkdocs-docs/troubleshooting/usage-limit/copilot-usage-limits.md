# Copilot Usage Limits Consumed Faster Under Usage-Based Billing

!!! warning "Symptoms"
    - Copilot usage quota nearly exhausted after only two days despite similar usage patterns as before
    - Noticeable change in consumption rate after migration to usage-based billing model

!!! info "Possible Causes"
    - The new usage-based billing model may count tokens/requests differently than the previous flat-rate or seat-based model
    - Background features (e.g., auto-completions, inline suggestions, chat interactions) may each consume quota separately
    - Changes in how "usage units" are defined (e.g., input + output tokens counted separately, premium model requests weighted higher)
    - Possible bug or misconfiguration in the billing/metering system after the transition

!!! tip "Recommended Actions"
    - Review the usage-based billing documentation to understand exactly what counts as a "unit" of usage
    - Check the usage dashboard/breakdown to identify which activities are consuming the most quota
    - Compare the billing metrics with actual usage patterns to determine if consumption is accurately tracked
    - Report the issue to the Copilot/billing team if consumption appears disproportionate to actual usage
    - Consider adjusting usage habits (e.g., reducing inline suggestions frequency) if the billing model penalizes certain interaction types
