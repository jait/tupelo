#!/usr/bin/env python
# vim: set sts=4 sw=4 et:
# -*- coding: utf-8 -*-
#
try:
    from PyQt4.QtGui import *
    from PyQt4 import QtCore
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
except ImportError:
    from PySide.QtGui import *
    from PySide import QtCore

from common import Card, Suit
from players import Player, CliPlayer
from common import STOPPED, VOTING, ONGOING
from common import GameState, CardSet, UserQuit, traced
from xmlrpc import XMLRPCCliPlayer
import threading


class SuitLabel(QLabel):

    def __init__(self, suit):
        QLabel.__init__(self)
        icon_name = suit.name + ".png"
        image = QImage(icon_name)
        #self.setScaledContents(True)
        self.pixmap = QPixmap.fromImage(image)
        self.setPixmap(self.pixmap.scaled(18, 18))
        policy = self.sizePolicy()
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    #def resizeEvent(self, ev):
    #    print "resize to %s", ev.size()
    #    QLabel.resizeEvent(self, ev)
    #    self.setPixmap(self.pixmap.scaled(ev.size()))
        #pixmap = self.pixmap.scaled(size)
        #self.setPixmap(pixmap)

    def heightForWidth(self, w):
        return w

class GCard(QWidget, Card):

    clicked = QtCore.Signal(Card)

    def __init__(self, suit, value, parent=None):
        QWidget.__init__(self, parent)
        Card.__init__(self, suit, value)
        label = QLabel(self.char)
        label.setScaledContents(True)
        layout = QHBoxLayout(self)
        icon = SuitLabel(self.suit)
        layout.addWidget(label)
        layout.addWidget(icon)
        layout.addStretch()
        #policy = self.sizePolicy()
        #policy.setHeightForWidth(True)
        #self.setSizePolicy(policy)

    def event(self, event):
        retval = QWidget.event(self, event)

        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.clicked.emit(self)
            retval = True

        return retval


class GGameState(GameState, QtCore.QObject):

    stateChanged = QtCore.Signal(GameState)
    trickPlayed = QtCore.Signal(GameState)

    def __init__(self):
        QtCore.QObject.__init__(self)
        GameState.__init__(self)

    @traced
    def update(self, new_state):
        GameState.update(self, new_state)
        self.stateChanged.emit(self)
        if len(self.table) == 4:
            self.trickPlayed.emit(self)


def gsynchronized(func):
    """
    A decorator to help with GUI synchronization.
    """
    def wrapper(self, *args, **kwargs):
        #print "calling"
        retval = func(self, *args, **kwargs)
        #print "called, waiting"
        self._wait_event.wait()
        self._wait_event.clear()
        #print "waited, returning"
        return retval

    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__

    return wrapper


class _GPlayerBase(QtCore.QObject):

    messageReceived = QtCore.Signal(str)
    handChanged = QtCore.Signal(CardSet)
    trickPlayed = QtCore.Signal(Player, GameState)

    def __init__(self, base):
        assert type(self) != _GPlayerBase, "This class must not be instantiated directly"
        QtCore.QObject.__init__(self)
        self.base = base
        self.game_state = GGameState()
        self._card_event = threading.Event()
        self._card_lock = threading.RLock()
        self._quit = False
        self._wait_event = threading.Event()

    def event_handled(self):
        self._wait_event.set()

    def vote(self):
        self.messageReceived.emit("It's voting time!")
        self._card_lock.release()
        try:
            self._wait_for_card()
        finally:
            self._card_lock.acquire()

    def play_card(self):
        self.messageReceived.emit("Your turn.")
        self._card_lock.release()
        try:
            self._wait_for_card()
        finally:
            self._card_lock.acquire()

    def _wait_for_card(self):
        """
        Wait for the user to play a card.
        """
        self._card_event.wait()
        self._card_event.clear()
        if self._quit:
            raise UserQuit()

    def run(self):
        """
        """
        self._card_lock.acquire()
        try:
            self.base.run(self)
        finally:
            self._card_lock.release()

    def quit(self):
        """
        Set quit flag and wake up the thread if waiting.
        """
        self._quit = True
        self._card_event.set()

    def play_a_card(self, card):
        # TODO: is there still a danger of deadlock here?
        if self._card_lock.acquire(False) == True:
            try:
                self.controller.play_card(self, card)
                self._card_event.set()
                self.handChanged.emit(self.hand)
            finally:
                self._card_lock.release()
    @traced
    def card_played(self, player, card, game_state):
        """
        Event handler for a played card.
        """
        if player.id == self.id:
            player_str = 'You'
        else:
            player_str = '%s' % player

        if game_state.state == VOTING:
            msg = '%s voted %s' % (player_str, card)
        else:
            msg = '%s played %s' % (player_str, card)

        self.messageReceived.emit(msg)
        self.game_state.update(game_state)

    @traced
    @gsynchronized
    def trick_played(self, player, game_state):
        self.game_state.update(game_state)
        self.trickPlayed.emit(player, game_state)

    def send_message(self, sender, msg):
        if sender is not None:
            msgstr = '%s: %s' % (sender, msg)
        else:
            msgstr = msg

        self.messageReceived.emit(msgstr)

class GPlayer(_GPlayerBase, CliPlayer):

    def __init__(self, name):
        CliPlayer.__init__(self, name)
        _GPlayerBase.__init__(self, CliPlayer)


class GXMLRPCPlayer(_GPlayerBase, XMLRPCCliPlayer):

    def __init__(self, name):
        XMLRPCCliPlayer.__init__(self, name)
        _GPlayerBase.__init__(self, XMLRPCCliPlayer)

