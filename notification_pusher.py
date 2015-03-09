from twisted.internet.protocol import Factory
from twisted.internet import protocol


class NotificationPusherProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)


class NotificationPusherFactory(Factory):
    protocol = NotificationPusherProtocol

    def __init__(self):
        self.clients = []

    def buildProtocol(self, addr):
        return NotificationPusherProtocol(self)

    def send_message(self, msg):
        for client in self.clients:
            client.transport.write(msg + "\n")
