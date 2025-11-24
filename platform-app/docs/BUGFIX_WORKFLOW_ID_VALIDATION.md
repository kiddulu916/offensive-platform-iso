# Bug Fix: Workflow ID Validation - Accept Periods/Dots

**Date:** 2025-11-18
**Status:** ✅ Fixed
**Severity:** Medium (blocked workflow creation with domain names)

## Problem

When creating workflows with domain names in the workflow ID (e.g., `webapp_full_t-mobile.com`), the application rejected the input with a validation error:

```
Error: 1 validation error for WorkflowDefinition
workflow_id
  Value error, workflow_id must contain only alphanumeric characters, hyphens, and underscores
  [type=value_error, input_value='webapp_full_t-mobile.com', input_type=str]
```

## Root Cause

**Overly Restrictive Validation in Pydantic Model**

The `WorkflowDefinition` and `WorkflowTask` models in `app/workflows/schemas.py` had validators that only allowed:
- Alphanumeric characters (a-z, A-Z, 0-9)
- Hyphens (-)
- Underscores (_)

Domain names require **periods (.)** which were being rejected.

### Code Before Fix

```python
@validator('workflow_id')
def validate_workflow_id(cls, v):
    """Ensure workflow_id is a valid identifier"""
    if not v.replace('_', '').replace('-', '').isalnum():
        raise ValueError("workflow_id must contain only alphanumeric characters, hyphens, and underscores")
    return v
```

**How it worked:**
1. Remove all underscores: `webapp_full_t-mobile.com` → `webappfullt-mobile.com`
2. Remove all hyphens: `webappfullt-mobile.com` → `webappfulltmobile.com`
3. Check if alphanumeric: `webappfulltmobile.com` ❌ **FAILS** (contains `.`)

The period from the domain name `.com` caused the validation to fail.

## Solution

**Updated Validation to Allow Periods**

Modified both `workflow_id` and `task_id` validators to accept periods (`.`) for domain names and file extensions.

### Code After Fix

```python
@validator('workflow_id')
def validate_workflow_id(cls, v):
    """Ensure workflow_id is a valid identifier"""
    # Allow alphanumeric, hyphens, underscores, and periods (for domain names)
    if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
        raise ValueError("workflow_id must contain only alphanumeric characters, hyphens, underscores, and periods")
    return v
```

**How it works now:**
1. Remove all underscores: `webapp_full_t-mobile.com` → `webappfullt-mobile.com`
2. Remove all hyphens: `webappfullt-mobile.com` → `webappfulltmobile.com`
3. Remove all periods: `webappfulltmobile.com` → `webappfulltmobilecom`
4. Check if alphanumeric: `webappfulltmobilecom` ✅ **PASSES**

## Changes Made

**File: `app/workflows/schemas.py`**

### 1. Updated `WorkflowDefinition.validate_workflow_id()` (Line 247-253)
- Added `.replace('.', '')` to allow periods
- Updated error message to include "and periods"

### 2. Updated `WorkflowTask.validate_task_id()` (Line 166-172)
- Added `.replace('.', '')` to allow periods
- Updated error message to include "and periods"

## Valid Examples After Fix

These workflow IDs now **pass validation**:

✅ `webapp_full_t-mobile.com`
✅ `scan_example.com`
✅ `test_192.168.1.1`
✅ `recon_api.github.com`
✅ `attack_10.0.0.1`
✅ `subdomain_enum_target.org`

These still **fail validation** (as intended):

❌ `webapp full` (contains space)
❌ `scan@example.com` (contains @)
❌ `test/path` (contains /)
❌ `attack:port` (contains :)

## Use Cases Enabled

This fix enables common security testing scenarios:

1. **Domain-based workflow IDs**: `webapp_scan_example.com`
2. **IP-based workflow IDs**: `portscan_192.168.1.1`
3. **Subdomain workflow IDs**: `recon_api.github.com`
4. **File extension IDs**: `parse_config.json`
5. **Version identifiers**: `test_v2.5.1`

## Testing

After the fix, workflows can be created with domain names:

```python
from app.workflows.schemas import WorkflowDefinition, WorkflowTask

# This now works!
workflow = WorkflowDefinition(
    workflow_id="webapp_full_t-mobile.com",
    name="Web App Scan - T-Mobile",
    target="t-mobile.com",
    tasks=[...]
)
```

## Alternative Approaches Considered

### Option A: Remove Validation Entirely (Rejected)
- Allow any characters in workflow_id
- **Problem:** Opens door to injection attacks, filesystem issues

### Option B: Use Regex Pattern (Rejected)
- Define explicit regex like `^[a-zA-Z0-9._-]+$`
- **Problem:** More complex, harder to understand

### Option C: Add Periods to Allowed Characters ✅ **Selected**
- Simple extension of existing logic
- Minimal code change
- Clear intent with comment

## Files Modified

- `app/workflows/schemas.py` - Updated validators for `workflow_id` and `task_id`
- `docs/BUGFIX_WORKFLOW_ID_VALIDATION.md` - This documentation

## Related Issues

This fix also resolves potential issues with:
- Task IDs containing domains
- Workflow IDs with version numbers (e.g., `scan_v1.2.3`)
- File-based identifiers (e.g., `parse_config.json`)

---

**Lesson Learned:** When validating identifiers in security tools, consider common target formats (domains, IPs, files) that may include periods.
