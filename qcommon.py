#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
from PyQt4.QtGui import *
from PyQt4 import QtCore
from common import Card, Suit
from players import CliPlayer
from common import STOPPED, VOTING, ONGOING
from common import GameState

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

class QCard(QWidget, Card):

    def __init__(self, suit, value, parent=None):
        QWidget.__init__(self, parent)
        Card.__init__(self, suit, value)
        label = QLabel(self.get_char())
        label.setScaledContents(True)
        layout = QHBoxLayout(self)
        icon = SuitLabel(self.suit)
        layout.addWidget(label)
        layout.addWidget(icon)
        layout.addStretch()
        #policy = self.sizePolicy()
        #policy.setHeightForWidth(True)
        #self.setSizePolicy(policy)


class GGameState(GameState, QtCore.QObject):

    stateChanged = QtCore.pyqtSignal(GameState)

    def __init__(self):
        GameState.__init__(self)
        QtCore.QObject.__init__(self)

    def update(self, new_state):
        GameState.update(self, new_state)
        self.stateChanged.emit(self)

        
class GPlayer(CliPlayer, QtCore.QObject):

    messageReceived = QtCore.pyqtSignal(str)

    def __init__(self, name):
        CliPlayer.__init__(self, name)
        QtCore.QObject.__init__(self)
        self.game_state = GGameState()
        self.game_state.stateChanged.connect(self.state_changed)

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
    
    def send_message(self, sender, msg):
        if sender is not None:
            msgstr = '%s: %s' % (sender, msg)
        else:
            msgstr = msg

        self.messageReceived.emit(msgstr)

    def state_changed(self, state):
        self.messageReceived.emit("state_changed()")

