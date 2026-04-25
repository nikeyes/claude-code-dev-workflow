from notification_service import NotificationService, RESTEndpoint


class TestNotificationService:
    def setup_method(self):
        self.service = NotificationService()

    def test_subscribe_and_notify(self):
        received = []
        self.service.subscribe("order.created", lambda p: received.append(p))
        self.service.notify("order.created", {"id": 1})
        assert received == [{"id": 1}]

    def test_unsubscribe(self):
        received = []
        cb = lambda p: received.append(p)
        self.service.subscribe("order.created", cb)
        self.service.unsubscribe("order.created", cb)
        self.service.notify("order.created", {"id": 1})
        assert received == []

    def test_subscriber_count(self):
        self.service.subscribe("x", lambda p: None)
        self.service.subscribe("x", lambda p: None)
        assert self.service.get_subscriber_count("x") == 2
        assert self.service.get_subscriber_count("y") == 0


class TestRESTEndpoint:
    def setup_method(self):
        self.service = NotificationService()
        self.endpoint = RESTEndpoint(self.service)

    def test_subscribe_endpoint(self):
        resp = self.endpoint.handle_request("POST", "/subscribe", {"event_type": "x"})
        assert resp["status"] == 200

    def test_notify_endpoint(self):
        resp = self.endpoint.handle_request("POST", "/notify", {"event_type": "x", "payload": {"a": 1}})
        assert resp["status"] == 200

    def test_not_found(self):
        resp = self.endpoint.handle_request("GET", "/missing")
        assert resp["status"] == 404
