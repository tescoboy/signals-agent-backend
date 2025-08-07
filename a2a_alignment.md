# A2A Protocol Alignment Plan

## Current Schema → A2A Mapping

Our current implementation maps cleanly to A2A concepts:

| Our Schema | A2A Concept | Notes |
|------------|-------------|-------|
| context_id | taskId | Already using unique IDs |
| context_type | Task type | discovery, activation, etc. |
| metadata | Task artifact | Results stored as JSON |
| parent_context_id | Related tasks | Task dependencies |
| created_at/expires_at | Task lifecycle | Timing tracking |

## Recommended Schema Enhancements

To prepare for A2A while maintaining current functionality:

```sql
-- Add status field for task lifecycle
ALTER TABLE contexts ADD COLUMN status TEXT 
  CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'expired'))
  DEFAULT 'completed';

-- Add completed_at for task timing
ALTER TABLE contexts ADD COLUMN completed_at TEXT;

-- Add artifact field for A2A outputs (optional, since we have metadata)
-- ALTER TABLE contexts ADD COLUMN artifact TEXT;
```

## A2A Message Wrapper

When Phase 3 implements A2A, wrap existing responses:

```python
def to_a2a_message(response: GetSignalsResponse, context_id: str) -> dict:
    """Convert our response to A2A message format."""
    return {
        "taskId": context_id,
        "status": "completed",
        "parts": [{
            "contentType": "application/json",
            "content": response.model_dump()
        }]
    }
```

## Benefits of Current Approach

1. **No Breaking Changes**: Current API remains stable
2. **A2A Ready**: Easy to add A2A wrapper when needed
3. **Best of Both**: AdCP-specific features + A2A compatibility
4. **Gradual Migration**: Can support both protocols simultaneously

## Phase 3 Implementation Path

1. Keep current schema (it's already good!)
2. Add status field for task lifecycle
3. Create A2A wrapper endpoints
4. Publish Agent Card for discovery
5. Support both AdCP and A2A protocols

This approach gives you A2A compatibility without losing the domain-specific benefits of your current implementation.