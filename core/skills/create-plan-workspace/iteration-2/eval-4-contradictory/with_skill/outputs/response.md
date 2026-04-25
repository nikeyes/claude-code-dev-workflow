# create-plan Response: Add real-time WebSocket notifications to the REST API

## Initial Analysis

I've read the task description and fully reviewed all three project files:

- `notification_service.py` — A simple in-process pub/sub `NotificationService` and a `RESTEndpoint` wrapper. Subscribers are stored in `self._subscribers`, a plain Python dict on the `NotificationService` instance. The REST layer currently does **not** wire subscriptions to actual callbacks — `POST /subscribe` returns a success response but never registers a callable.
- `test_notification_service.py` — Tests for subscribe/unsubscribe/notify behavior and the REST endpoint routes.
- `Makefile` — Runs `pytest test_notification_service.py -v`.

---

## Contradictory Requirements — Stopping for Clarification

Before writing any plan I need to flag a **fundamental contradiction** in the requirements:

> "The system must remain stateless with no server-side session storage, **but** WebSocket connections need to persist user state between messages."

These two constraints are mutually exclusive as written. Here is the conflict broken down:

### The Contradiction

| Requirement | What it implies |
|---|---|
| "Stateless — no server-side session storage" | The server must not store any per-user information between requests. Each request is self-contained. This is the REST/HTTP constraint from Roy Fielding's architectural style. |
| "WebSocket connections must persist user state between messages" | A WebSocket is a long-lived, stateful connection. The server **must** track which user owns which connection and what state (subscriptions, auth, context) is associated with that connection. |

A WebSocket connection by its nature IS server-side state. There is no way to have a persistent WebSocket connection without the server tracking it. The two requirements cannot both be true at the same time.

### What "stateless" Likely Means (Possible Interpretations)

I can see at least three different things the author might have meant:

1. **Stateless REST endpoints only** — The HTTP REST endpoints remain stateless (no sessions, no cookies for REST calls), but the WebSocket subsystem is allowed to hold connection state. This is the most common real-world architecture and is technically coherent.

2. **No persistent server-side database for session/state** — User state lives only in the WebSocket connection object itself (in memory, for the duration of the connection), not in Redis/a database. When the connection drops, state is gone. This is "stateless" in the sense of "no external session store."

3. **Stateless authentication** — Each WebSocket message must carry a self-contained auth token (e.g., JWT) so the server does not maintain an auth session. The connection itself may still hold subscription state.

Each interpretation leads to a different architecture. Writing a plan without knowing which one is intended would produce the wrong design.

### Additional Questions Raised by the Codebase

Beyond the contradiction, I found a gap between the ticket and the existing code worth raising:

1. **The current `POST /subscribe` endpoint is non-functional for push notifications.** It accepts an `event_type` but never registers a callback. For WebSocket notifications to work, there must be a mechanism to associate a WebSocket connection with the `NotificationService` subscriber list. What should happen to the existing REST subscribe/notify API — does it stay, get removed, or co-exist with the WebSocket API?

2. **There is no concept of "user" anywhere in the codebase.** `NotificationService` and `RESTEndpoint` have no user identity, authentication, or authorization. Does "persist user state" mean we need to add user identity? If so, what is the auth mechanism (JWT, API key, session cookie)?

3. **Deployment context**: WebSockets require a long-running server process. The current code is a pure in-process library. What server framework is in use or planned (FastAPI, Django Channels, aiohttp, plain asyncio)?

---

## Questions That Must Be Resolved Before Planning

1. **Which interpretation of "stateless" applies?**
   - (a) REST endpoints stateless, WebSocket layer may hold connection state
   - (b) No external session store (Redis/DB), but in-memory connection state is OK
   - (c) Every WebSocket message must be self-authenticating (JWT per message)

2. **What counts as "user state" that must persist between messages?**
   - Just the list of subscribed event types?
   - Authentication/identity?
   - Accumulated message history?
   - Something else?

3. **Should the existing REST subscribe/notify API remain as-is, be deprecated, or be replaced by the WebSocket API?**

4. **What Python web framework will host the WebSocket server?** (FastAPI with WebSockets, Django Channels, Starlette, etc.)

5. **Is there a user authentication system already?** If so, where does it live?

---

## Summary

I cannot write a sound implementation plan until the contradiction between "stateless" and "persist user state over WebSocket" is resolved. The most likely intended meaning is interpretation (a) or (b) above, but assuming the wrong one would produce an incorrect design. Please clarify which definition of "stateless" applies and what "user state" means in this context, and I will proceed immediately to a full plan.
