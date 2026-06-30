---
layout: home
title: Home
nav_order: 1
---

# AI Core Troubleshooting
{: .no_toc }

Troubleshooting guides and tutorials for SAP AI Core — covering timeout issues, rate limits, orchestration, and grounding.

---

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Timeout Issues

Issues related to LLM request timeouts and 503 errors.

| Issue | Description |
|-------|-------------|
| [LLM Requests Timing Out Silently](docs/troubleshooting-guide#issue-llm-requests-timing-out-silently) | Requests time out intermittently with no error message returned |
| [Orchestration Model Timeout and 503 Errors](docs/troubleshooting-guide#issue-orchestration-model-timeout-and-503-errors) | 600-second timeout exceeded, intermittent 503 errors |

---

## Rate Limit Issues

Issues related to rate limiting and usage quotas.

| Issue | Description |
|-------|-------------|
| [Rate Limited at ~100 RPM Despite 2,000 RPM Quota](docs/troubleshooting-guide#issue-rate-limited-at-100-rpm-despite-2000-rpm-configured-quota) | Actual throughput capped at ~100 RPM regardless of configured quota |
| [Unable to Increase Rate Limit (Error 100401)](docs/troubleshooting-guide#issue-unable-to-increase-rate-limit-error-100401) | Rate limit increase requests fail with error code 100401 |
| [Copilot Usage Limits Consumed Faster](docs/troubleshooting-guide#issue-copilot-usage-limits-consumed-faster-under-usage-based-billing) | Quota exhausted faster after migration to usage-based billing |

---

## Orchestration

| Guide | Description |
|-------|-------------|
| [AI Core Orchestration with Grounding](docs/ai-core-orchestration-with-grounding) | Set up orchestration pipelines with grounding capabilities |
