---
layout: default
title: Orchestration with Grounding
nav_order: 3
---

# AI Core Orchestration with Grounding
{: .no_toc }

<details open markdown="block">
  <summary>Table of contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## Overview

This guide covers how to set up AI Core orchestration with grounding capabilities.

---

## Prerequisites
{: .text-purple-300 }

- SAP AI Core instance
- Access to SAP AI Launchpad
- Basic knowledge of LLM orchestration

---

## Steps

### 1. Set Up Your Environment

Ensure your AI Core environment is configured correctly.

### 2. Configure Grounding

Add your grounding configuration to the orchestration pipeline.

### 3. Run the Orchestration

Trigger and monitor your orchestration workflow.

---

## Troubleshooting
{: .text-purple-300 }

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Token expired | Regenerate the OAuth token |
| `404 Not Found` | Wrong deployment URL | Verify the deployment ID in AI Launchpad |
| `503 Service Unavailable` | Model not deployed | Check deployment status in AI Core |

---

## References

- [SAP AI Core Documentation](https://help.sap.com/docs/ai-core)
