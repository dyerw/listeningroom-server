from twisted.internet.protocol import Factory
from twisted.internet import reactor, protocol
from twisted.web import server, resource


class Room(resource.Resource):
    def __init__(self, notifications):
        resource.Resource.__init__(self)
        self.notifications = notifications

    def render_GET(self, request):
        self.notifications.send_message("Someone got me\n")
        return "GOT ME!"

    def render_POST(self, request):
        return "POST ME!"


class NotificationProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)


class NotificationFactory(Factory):
    protocol = NotificationProtocol

    def __init__(self):
        self.clients = []

    def buildProtocol(self, addr):
        return NotificationProtocol(self)

    def send_message(self, msg):
        for client in self.clients:
            client.transport.write(msg)


if __name__ == "__main__":
    root = resource.Resource()
    notification_factory = NotificationFactory()
    root.putChild("room", Room(notification_factory))
    reactor.listenTCP(5001, server.Site(root))
    reactor.listenTCP(5002, notification_factory)
    reactor.run()