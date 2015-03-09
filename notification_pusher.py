import json

from twisted.internet.protocol import Factory
from twisted.internet import protocol


class NotificationPusherProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.channel = None

    def connectionMade(self):
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)
        if self.channel:
            self.factory.channels[self.channel].remove(self)

    def dataReceived(self, data):
        print data
        try:
            # Used to subscribe to a new channel
            data = json.loads(data)
            channel = data['channel']

            # If we are not already subscribed to this channel
            if channel != self.channel:
                # If we are subscribed to another channel, remove
                # us first
                if self.channel:
                    self.factory.channels[self.channel].remove(self)

                # Register ourselves for that channel in the factory
                if channel not in self.factory.channels:
                    self.factory.channels[channel] = []
                self.factory.channels[channel].append(self)

        except ValueError:
            # We got something that wasn't JSON, ignore it
            pass


class NotificationPusherFactory(Factory):
    protocol = NotificationPusherProtocol

    def __init__(self):
        self.clients = []
        self.channels = {}

    def buildProtocol(self, addr):
        return NotificationPusherProtocol(self)

    def send_message(self, channel, msg):
        if channel in self.channels:
            for client in self.channels[channel]:
                client.transport.write(msg + "\n")
