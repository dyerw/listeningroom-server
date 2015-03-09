import json

from twisted.internet.protocol import Factory
from twisted.internet import reactor, protocol
from twisted.web import server
from klein import Klein

HTTP_PORT = 5001
TCP_PORT = 5002


class ListeningRoomHTTPServer(object):
    """
    This object handles all HTTP request routing.
    """
    app = Klein()

    def __init__(self, notification_pusher_factory):
        self.notification_pusher_factory = notification_pusher_factory

    @app.route('/room/<room_id>', methods=['GET'])
    def get_room_info(self, request, room_id):
        self.notification_pusher_factory.send_message("Someone wants to know!\n")
        request.setHeader('Content-Type', 'application/json')
        return json.dumps({'room_id': room_id})


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
            client.transport.write(msg)


if __name__ == "__main__":
    notification_pusher_factory = NotificationPusherFactory()
    http_server = ListeningRoomHTTPServer(notification_pusher_factory)
    reactor.listenTCP(HTTP_PORT, server.Site(http_server.app.resource()))
    reactor.listenTCP(TCP_PORT, notification_pusher_factory)
    reactor.run()