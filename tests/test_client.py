
from penne.client import create_client
from penne.handlers import handle
from penne.delegates import *

from delegates import TableDelegate


class Tests:

    test_client = create_client("ws://localhost:50000", {"tables": TableDelegate}, strict=True)
    test_messages = [
        (0, {})
    ]

    def test_client_init(self, client):
        assert isinstance(client, Client)
        assert "document" in client.state
        assert client.is_shutdown is False
        assert client.callback_queue.empty()
        assert len(client.delegates) == 14
        assert len(client.server_messages) == 36

    def test_create_client_with_delegates(self):
        delegates = {"tables": TableDelegate}
        client = create_client("ws://localhost:50000", strict=False, custom_delegate_hash=delegates)
        self.test_client_init(client)
        assert client.strict is False
        assert client.delegates["tables"] == TableDelegate
        client.shutdown()
        client.thread.join()

    def test_create_client_with_delegates_and_on_connected(self):
        delegates = {"tables": TableDelegate}
        client = create_client("ws://localhost:50000", strict=True, custom_delegate_hash=delegates, on_connected=lambda: print())
        self.test_client_init(client)
        assert client.strict is True
        assert client.delegates["tables"] == TableDelegate
        assert client.on_connected is not None
        client.shutdown()
        client.thread.join()

    def test_handle(self, tag, message):
        pass

    def test_handle_messages(self):
        for message_tuple in self.test_messages:
            handle(self.test_client, *message_tuple)
            self.test_handle(*message_tuple)

    def test_client_object_from_name(self):
        assert self.test_client.get_object_from_name("Test Method") == self.test_client.state[MethodID(0, 0)]

