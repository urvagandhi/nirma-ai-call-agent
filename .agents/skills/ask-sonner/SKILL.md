---
name: ask-sonner
description: Guide to Sonner, the React toast library — install and wire up the Toaster, pick the right toast() call, promise and loading toasts, updating, dismissing and persisting toasts.
---

# Working With Sonner

## Setup
1. **One `<Toaster />`, mounted once** as close to the root as possible (`App.tsx`). Never render conditionally or per-page.
2. **`toast()` called from client code** (event handlers, WebSocket callbacks, async dispatches).

```jsx
import { Toaster, toast } from 'sonner';
```

## Best Patterns for Call Agent Actions
- **Async Dispatching**:
```jsx
toast.promise(dispatchCampaign(campaignId), {
  loading: 'Queuing campaign calls with carrier...',
  success: (data) => `Campaign active: ${data.total_calls} queued`,
  error: (err) => `Failed to dispatch: ${err.message}`,
});
```
- **Real-Time Call Alerts**:
```jsx
toast.info('Inbound call answered', { description: 'Student: Aarav Patel (+91 98765 43210)' });
```
