# Implementation Plan: Real-Time WebSocket Notifications

## Contradiction Identified

The requirements contain a direct conflict that must be resolved before implementation begins:

- **Requirement A:** The system must remain stateless with no server-side session storage.
- **Requirement B:** WebSocket connections need to persist user state between messages.

WebSocket connections are inherently stateful. The TCP connection itself is a persistent, server-side resource. Maintaining a WebSocket connection *is* server-side state — you cannot have a WebSocket and simultaneously claim no server-side session storage exists.

**Decision required (pick one):**

1. **Relax the stateless requirement for WebSocket connections only.** The REST API remains stateless. The WebSocket layer is allowed to hold in-memory connection state (connection ID, user identity, subscriptions) for the lifetime of the connection. This state is ephemeral, not persisted to a database, and is lost on server restart or disconnect. This is the most practical resolution.

2. **Abandon true WebSockets in favour of stateless push alternatives.** Use Server-Sent Events (SSE) combined with a JWT-authenticated event stream, where the client re-authenticates on reconnect and the server holds no session. Or use polling. These satisfy the stateless constraint but lose true bidirectional messaging.

**This plan proceeds with Option 1** — REST stays stateless; WebSocket connections hold ephemeral in-memory state only. If the product requirement truly forbids any server-side state, the team must revisit whether WebSockets are the right technology at all.

---

## Current Codebase Summary

`notification_service.py` provides two classes:

- `NotificationService` — in-memory pub/sub with subscribe, unsubscribe, notify, and subscriber count.
- `RESTEndpoint` — thin HTTP routing layer delegating to `NotificationService`.

The existing `RESTEndpoint._handle_subscribe` method currently does nothing useful: it returns `{"subscribed": True}` but never registers a callback with `NotificationService`. Real subscriptions are not wired up through the HTTP layer.

The tests cover basic pub/sub behaviour and HTTP routing but do not test the subscribe endpoint actually delivering notifications.

---

## Implementation Plan

### Phase 1: Fix the existing REST subscribe endpoint

The current `_handle_subscribe` accepts an `event_type` but never registers a callback. Before adding WebSockets, this should be fixed or explicitly acknowledged as intentional (e.g., subscriptions come only via WebSocket). Document the intent either way.

**Step 1.1 — Decide subscription model**

Option A: REST-only subscribers use a persistent store (message queue, database) — this conflicts with stateless but is common in practice.
Option B: REST `POST /subscribe` is removed or deprecated; all subscriptions happen over WebSocket.

Recommendation: Go with Option B. Remove or no-op the REST subscribe endpoint. Subscriptions live only for the duration of a WebSocket connection.

**Step 1.2 — Add a test for the broken behaviour first**

Write a failing test that proves `POST /subscribe` does not actually cause `notify` to deliver a message to that subscriber. This makes the defect explicit before the refactor.

---

### Phase 2: Add a WebSocket connection manager

Create a `WebSocketConnectionManager` class responsible for:

- Registering a new connection (connection ID, authenticated user identity).
- Associating a connection with one or more event type subscriptions.
- Removing a connection on disconnect.
- Looking up which connections are subscribed to a given event type.

This class holds ephemeral in-memory state. It is the only place where server-side session state lives. It is not a "session store" in the traditional sense — there is no persistence, no TTL management, and no cross-request identity tracking.

```python
class WebSocketConnectionManager:
    def __init__(self):
        self._connections: dict[str, dict] = {}  # conn_id -> {user_id, subscriptions}

    def connect(self, connection_id: str, user_id: str) -> None: ...
    def disconnect(self, connection_id: str) -> None: ...
    def subscribe(self, connection_id: str, event_type: str) -> None: ...
    def get_connections_for_event(self, event_type: str) -> list[str]: ...
```

**Step 2.1 — Write tests for WebSocketConnectionManager first**

Cover: connect/disconnect lifecycle, subscribe/unsubscribe per connection, querying connections by event type, handling unknown connection IDs gracefully.

---

### Phase 3: Integrate WebSocketConnectionManager with NotificationService

`NotificationService.notify` currently calls registered callbacks. For WebSocket delivery, the callback will be a send function that writes to the open WebSocket connection.

Wire them together:

```python
def register_websocket_sender(manager: WebSocketConnectionManager, service: NotificationService, send_fn: Callable[[str, dict], None]):
    def ws_delivery(payload: dict, event_type: str):
        for conn_id in manager.get_connections_for_event(event_type):
            send_fn(conn_id, payload)
    # register ws_delivery as a subscriber for each event type dynamically
```

This keeps `NotificationService` unchanged and avoids coupling it to WebSocket concerns.

**Step 3.1 — Test integration with a fake send function**

Use a simple list-appending fake for `send_fn`. No mocking frameworks needed; the existing test style in the codebase uses plain lambdas.

---

### Phase 4: Authentication — stateless token validation per connection

Since the REST API is stateless, authentication uses tokens (JWT or similar). WebSocket connections must authenticate at handshake time.

**Step 4.1 — Extract a `validate_token(token: str) -> str | None` function**

Returns the user ID if the token is valid, or `None`. This function is stateless — it validates the token signature, does not look up a session.

**Step 4.2 — Apply at WebSocket handshake**

The client sends a token in the connection query string or first message. The server validates it before calling `WebSocketConnectionManager.connect`. If validation fails, close the connection immediately.

No session is stored: the user ID derived from the token is held only in `_connections` for the duration of the WebSocket connection.

---

### Phase 5: WebSocket protocol (message format)

Define a simple JSON protocol for messages over the WebSocket:

```json
// Client -> Server: subscribe to an event type
{"action": "subscribe", "event_type": "order.created"}

// Client -> Server: unsubscribe
{"action": "unsubscribe", "event_type": "order.created"}

// Server -> Client: notification delivery
{"event_type": "order.created", "payload": {"id": 42}}

// Server -> Client: error
{"error": "unknown action"}
```

**Step 5.1 — Write a message parser/validator**

A pure function `parse_client_message(raw: str) -> dict | None` that returns a validated message dict or `None` on parse failure. Test this independently of WebSocket mechanics.

---

### Phase 6: Hook into a web framework

The above components are framework-agnostic. Wire them into a real WebSocket server using FastAPI + `websockets`, or Flask-SocketIO, or similar.

The `RESTEndpoint` already handles plain HTTP routes. Add a `/ws` WebSocket endpoint that:

1. Validates the token from the connection request.
2. Calls `WebSocketConnectionManager.connect`.
3. Loops receiving messages and dispatching to subscribe/unsubscribe handlers.
4. Calls `WebSocketConnectionManager.disconnect` on close.

**This phase is where the framework-specific code lives. Keep it thin — all real logic lives in the classes above.**

---

## File Changes Summary

| File | Change |
|---|---|
| `notification_service.py` | No changes to `NotificationService`. Optionally deprecate `RESTEndpoint._handle_subscribe`. |
| `websocket_connection_manager.py` | New file — `WebSocketConnectionManager` class. |
| `test_websocket_connection_manager.py` | New file — tests for connection manager. |
| `token_validator.py` | New file — stateless token validation. |
| `websocket_handler.py` | New file — WebSocket protocol parser and handler, wired to manager + service. |
| `test_notification_service.py` | Add test exposing broken subscribe endpoint behaviour. |
| `app.py` | New or modified — framework integration, routes for REST + `/ws`. |

---

## What This Plan Does Not Do

- It does not add horizontal scaling support (multiple server instances). If that is needed, the `WebSocketConnectionManager` must be backed by Redis pub/sub or a similar shared store — which would reintroduce the "session storage" concern. This is a separate decision.
- It does not define the token format or signing key management.
- It does not address reconnection logic on the client side.

These are deliberate deferments, not omissions. They should be addressed in follow-on planning once the core WebSocket infrastructure is proven.
