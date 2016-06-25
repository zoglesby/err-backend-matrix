# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import time
import logging

from errbot.errBot import ErrBot
from errbot.backends.base import Message, Person, Room, RoomOccupant
from errbot.backends.base import Identifier

log = logging.getLogger('errbot.backends.matrix')

try:
    from matrix_client.client import MatrixClient
    from matrix_client.api import MatrixRequestError
except ImportError as _:
    log.exception("Could not start the Matrix backend.")
    log.fatal("""
    If you intend to use the Matrix backend please install
    matrix-client from PyPI.
    """)
    sys.exit(1)


class MatrixIdentifier(Identifier):
    def __init__(self, id):
        self._id = id

    @property
    def id(self):
        return self._id

    def __unicode__(self):
        return str(self._id)

    def __eq__(self, other):
        return self._id == other.id

    __str__ = __unicode__

    aclattr = id

class MatrixPerson(Person):
    def __init__(self, mc, user_id=None, room_id=None):
        self._userid = user_id
        self._roomid = room_id
        self._username = "PERSON_USERNAME"
        self._nick = "PERSON_NICK"
        self._mc = mc

    @property
    def userid(self):
        return self._userid

    @property
    def username(self):
        return self._username

    @property
    def channelid(self):
        log.info("channel id !!!")
        self._roomid

    @property
    def client(self):
        # TODO: Check if this can be acquired.
        return None

    @property
    def fullname(self):
        # TODO: Currently a user's full name/real name cannot be acquired, but
        #       in future this might change.
        return None

    @property
    def nick(self):
        # TODO: Handle weird Unicode nicknames (like @skaverat's), better in
        #       future.
        return self._nick

    def __unicode__(self):
        return "@%s" % self._username

    def __str__(self):
        return self.__unicode__()

    @property
    def person(self):
        return "%s" % self._userid

    # Override for ACLs
    @property
    def aclattr(self):
        return "@%s" % self.username

    # Compatibility with the generic API.
    client = channelid
    nick = username


class MatrixRoomOccupant(MatrixPerson, RoomOccupant):
    def __init__(self, room, username=None, nick=None):
        self._room = room
        super().__init__(username, nick)

    @property
    def room(self):
        return self._room

    def __unicode__(self):
        return "Room Occupant"


class MatrixRoom(MatrixIdentifier, Room):
    def __init__(self, id):
        super().__init__(id)

    @property
    def id(self):
        return self._id

    def join(self, username=None, password=None):
        log.debug("Joining room %s" % self.id)

    def __unicode__(self):
        return "Room"


class MatrixBackend(ErrBot):
    def __init__(self, config):
        super().__init__(config)

        if not hasattr(config, 'MATRIX_HOMESERVER'):
            log.fatal("""
            You need to specify a homeserver to connect to in
            config.MATRIX_HOMESERVER.

            For example:
            MATRIX_HOMESERVER = "https://matrix.org"
            """)
            sys.exit(1)

        self._homeserver = config.MATRIX_HOMESERVER
        self._username = config.BOT_IDENTITY['username']
        self._password = config.BOT_IDENTITY['password']


    def serve_once(self):
        def dispatch_event(event):
            log.info("Received event: %s" % event)

            if event['type'] == "m.room.member":
                if event['membership'] == "invite" and event['state_key'] == self._client.user_id:
                    room_id = event['room_id']
                    self._client.join_room(room_id)
                    log.info("Auto-joined room: %s" % room_id)

            if event['type'] == "m.room.message" and event['sender'] != self._client.user_id:
                sender = event['sender']
                room_id = event['room_id']
                body = event['content']['body']
                log.info("Received message from %s in room %s" % (sender, room_id))

                # msg = Message(body)
                # msg.frm = MatrixPerson(self._client, sender, room_id)
                # msg.to = MatrixPerson(self._client, self._client.user_id, room_id)
                # self.callback_message(msg) 

                msg = self.build_message(body)
                room = MatrixRoom(room_id)
                msg.frm = MatrixRoomOccupant(room, sender)
                msg.to = room
                self.callback_message(msg) 

        self.reset_reconnection_count()
        self.connect_callback()

        self._client = MatrixClient(self._homeserver)

        try:
            self._token = self._client.register_with_password(self._username,
                                                              self._password,)
        except MatrixRequestError as e:
            if e.code == 400:
                try:
                    self._token = self._client.login_with_password(self._username,
                                                     self._password,)
                except MatrixRequestError:
                    log.fatal("""
                        Incorrect username or password specified in
                        config.BOT_IDENTITY['username'] or config.BOT_IDENTITY['password'].
                    """)
                    sys.exit(1)

        self.bot_identifier = MatrixPerson(self._client)

        user = self._client.get_user(self._client.user_id)
        user.set_presence()
        self._client.add_listener(dispatch_event)

        try:
            while True:
                self._client.listen_for_events()
        except KeyboardInterrupt:
            log.info("Interrupt received, shutting down...")
            return True
        finally:
            self.disconnect_callback()

    def rooms(self):
        rooms = []
        raw_rooms = self._client.get_rooms()

        for rid, robject in raw_rooms:
            # TODO: Get the canonical alias rather than the first one from
            #       `Room.aliases`.
            log.debug('Found room %s (aka %s)' % (rid, rid.aliases[0]))

    def send_message(self, mess):
        log.info("send_message")

        super().send_message(mess)
        room = self._client.join_room(mess.to.room.id)
        room.send_text(mess.body)

    def connect_callback(self):
        super().connect_callback()

    def build_identifier(self, txtrep):
        raise Exception(
            "XXX"
        )

    def build_reply(self, mess, text=None, private=False):
        log.info("build_reply")

        print(private)
        print(mess.frm)
        print(mess.to)

        response = self.build_message(text)
        response.frm = self.bot_identifier
        response.to = mess.frm
        return response

    def change_presence(self, status: str = '', message: str = ''):
        raise Exception(
            "XXX"
        )

    @property
    def mode(self):
        return 'matrix'

    def query_room(self, room):
        raise Exception(
            "XXX"
        )

