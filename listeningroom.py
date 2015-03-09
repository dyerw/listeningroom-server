import json

import redis
from twisted.internet import reactor
from twisted.web import server
from klein import Klein

from notification_pusher import NotificationPusherFactory

HTTP_PORT = 5001
TCP_PORT = 5002
REDIS_HOST = 'localhost'
REDIS_PORT = 6379


class ListeningRoomHTTPServer(object):
    """
    This object handles all HTTP request routing.
    """
    app = Klein()

    def __init__(self, notification_pusher_factory, redis_connection):
        self.redis_connection = redis_connection
        self.notification_pusher_factory = notification_pusher_factory

    # Register routes
    @app.route('/room/<room_id>', methods=['GET'])
    def get_room(self, request, room_id):
        request.setHeader('Content-Type', 'application/json')
        return self.get_room_info(room_id)

    @app.route('/room/<room_id>/<song_id>', methods=['POST'])
    def post_room(self, request, room_id, song_id):
        request.setHeader('Content-Type', 'application/json')
        return self.add_song_to_queue(room_id, song_id)

    def add_song_to_queue(self, room_id, song_id):
        if not self.room_exists(room_id):
            return json.dumps({'error': 'room does not exist'})

        # Add the song to the queue
        r.rpush(room_id + ':future_song_queue', song_id)

        # Update other users that song has been added
        self.notification_pusher_factory.send_message(room_id, json.dumps({'song_added': song_id}))

        return self.get_room_info(room_id)

    def get_room_info(self, room_id):
        """
        Get the current room state for a given id, if it does not exist yet
        create that room in the model and return a blank state
        :param room_id: the name of the room we want info for
        :return: json string of the info about the room
        """
        if not self.room_exists(room_id):
            # Register the room in the list of rooms
            self.redis_connection.rpush('rooms', room_id)

            # Return empty data
            return self.json_room_info(None, None, None)
        else:
            # Get relevant room info
            future_song_queue = self.redis_connection.lrange(room_id + ':future_song_queue', 0, -1)
            past_song_queue = self.redis_connection.lrange(room_id + ':past_song_queue', 0, -1)
            current_song = self.redis_connection.get(room_id + ':current_song')
            return self.json_room_info(future_song_queue, past_song_queue, current_song)

    def room_exists(self, room_id):
        # Get entire list
        rooms = self.redis_connection.lrange('rooms', 0, -1)
        if rooms is None:
            return False
        return room_id in rooms

    def json_room_info(self, future_song_queue, past_song_queue, current_song):
        return json.dumps({'future_song_queue': future_song_queue,
                           'past_song_queue': past_song_queue,
                           'current_song': current_song})


if __name__ == "__main__":
    # Setup a connection to Redis server
    r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)

    # We create an object to manage all our TCP clients
    notification_pusher_factory = NotificationPusherFactory()

    # We create an HTTP server with knowledge of the TCP server
    # and knowledge of the Redis server
    http_server = ListeningRoomHTTPServer(notification_pusher_factory, r)

    # We set them listening on their respective ports
    reactor.listenTCP(HTTP_PORT, server.Site(http_server.app.resource()))
    reactor.listenTCP(TCP_PORT, notification_pusher_factory)

    # We start the event loop
    reactor.run()