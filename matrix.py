# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import time
import logging

from errbot.errBot import ErrBot
from errbot.backends.base import Message, Person, Room, RoomOccupant

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


class MatrixPerson(Person):
    def __init__(self, username=None, nick=None):
        self._username = username
        self._nick = nick

    @property
    def username(self):
        return self._username

    # Generic API
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

    @property
    def person(self):
        return self._username

    aclattr = username


class MatrixRoomOccupant(MatrixPerson, RoomOccupant):
    def __init__(self, room, username=None, nick=None):
        self._room = room
        super().__init__(username, nick)

    @property
    def room(self):
        return self._room


class MatrixRoom(Room):
    def __init__(self, idd):
        self._idd = idd

    def join(self, username=None, password=None):
        log.debug("Joining room %s" % self._idd)


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
        self.connect_callback()

        try:
            self._client = MatrixClient(self._homeserver)
            self._token = self._client.register_with_password(self._username,
                                                              self._password,)
        except MatrixRequestError as e:
            if e.code == 400:
                try:
                    self._client.login_with_password(self._username,
                                                     self._password,)
                except MatrixRequestError:
                    log.fatal("""
                        Incorrect username or password specified in
                        config.BOT_IDENTITY['username'] or config.BOT_IDENTITY['password'].
                    """)
                    sys.exit(1)

        self._client.add_listener(dispatch_matrix_event)
        try:
            while True:
                self._client.start_listener_thread()
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
        super().send_message(mess)

    def connect_callback(self):
        super().connect_callback()

    def build_identifier(self, txtrep):
        raise Exception(
            "You found a bug. I expected at least one of userid, channelid, username or channelname "
            "to be resolved but none of them were. This shouldn't happen so, please file a bug."
        )

    def build_reply(self, mess, text=None, private=False):
        raise Exception(
            "You found a bug. I expected at least one of userid, channelid, username or channelname "
            "to be resolved but none of them were. This shouldn't happen so, please file a bug."
        )

    def change_presence(self, status: str = '', message: str = ''):
        raise Exception(
            "You found a bug. I expected at least one of userid, channelid, username or channelname "
            "to be resolved but none of them were. This shouldn't happen so, please file a bug."
        )

    @property
    def mode(self):
        return 'matrix'

    def query_room(self, room):
        raise Exception(
            "You found a bug. I expected at least one of userid, channelid, username or channelname "
            "to be resolved but none of them were. This shouldn't happen so, please file a bug."
        )

def _dispatch_matrix_event(event):
    log.info("Received event from Matrix")

