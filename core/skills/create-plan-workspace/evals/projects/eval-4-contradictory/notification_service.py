from typing import Callable


class NotificationService:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb is not callback
            ]

    def notify(self, event_type: str, payload: dict) -> int:
        callbacks = self._subscribers.get(event_type, [])
        for cb in callbacks:
            cb(payload)
        return len(callbacks)

    def get_subscriber_count(self, event_type: str) -> int:
        return len(self._subscribers.get(event_type, []))


class RESTEndpoint:
    def __init__(self, notification_service: NotificationService):
        self._service = notification_service
        self._routes = {
            "POST /subscribe": self._handle_subscribe,
            "POST /notify": self._handle_notify,
            "GET /subscribers": self._handle_get_count,
        }

    def handle_request(self, method: str, path: str, body: dict = None) -> dict:
        route_key = f"{method} {path}"
        handler = self._routes.get(route_key)
        if handler is None:
            return {"status": 404, "body": {"error": "Not found"}}
        return handler(body or {})

    def _handle_subscribe(self, body: dict) -> dict:
        event_type = body.get("event_type")
        if not event_type:
            return {"status": 400, "body": {"error": "event_type required"}}
        return {"status": 200, "body": {"subscribed": True, "event_type": event_type}}

    def _handle_notify(self, body: dict) -> dict:
        event_type = body.get("event_type")
        payload = body.get("payload", {})
        if not event_type:
            return {"status": 400, "body": {"error": "event_type required"}}
        count = self._service.notify(event_type, payload)
        return {"status": 200, "body": {"notified": count}}

    def _handle_get_count(self, body: dict) -> dict:
        event_type = body.get("event_type", "")
        count = self._service.get_subscriber_count(event_type)
        return {"status": 200, "body": {"count": count}}
