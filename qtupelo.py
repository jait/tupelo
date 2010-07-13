#!/usr/bin/env python
# vim: set sts=4 sw=4 et:
# -*- coding: utf-8 -*-
#
import sys
import time
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from qcommon import GCard, GPlayer, GXMLRPCPlayer
import common
import xmlrpc
import logging
from game import GameController
from players import DummyBotPlayer, CountingBotPlayer

class GTable(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setLayout(QGridLayout())

    def draw_cards(self, cardset, player_id):
        # (row, col)
        left = (1, 0)
        top = (0, 1)
        right = (1, 2)
        bottom = (2, 1)

        places = [left, top, right, bottom]
        my_place = places.index(bottom)

        for widget in self.findChildren(QWidget):
            widget.deleteLater()

        # place where we start drawing
        my_card = None
        for card in cardset:
            if card.played_by is not None and card.played_by.id == player_id:
                my_card = cardset.index(card)

        if my_card is not None:
            index = (my_place - my_card) % 4
        else:
            index = (my_place - len(cardset)) % 4

        for card in cardset:
            gcard = GCard(card.suit, card.value, parent=self)
            place = places[index]
            self.layout().addWidget(gcard, place[0], place[1])
            index = (index + 1) % 4

class TupeloApp(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.resize(640, 480)
        self.setWindowTitle("Tupelo")

        hbox = QHBoxLayout(self)
        vbox_widget = QWidget()
        vbox = QVBoxLayout(vbox_widget)

        self.status_area = QLabel()
        vbox.addWidget(self.status_area, 0, Qt.AlignTop)

        self.table = GTable()
        vbox.addWidget(self.table, 1)

        self.hand_widget = QWidget()
        self.hand = QHBoxLayout(self.hand_widget)

        vbox.addWidget(self.hand_widget)

        hbox.addWidget(vbox_widget)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        hbox.addWidget(self.text)
        self.create_game(True)
        self.draw_hand()
       
    def create_game(self, remote=False):
        if remote:
            game = xmlrpc.XMLRPCProxyController('http://localhost:8052')
            self.player = GXMLRPCPlayer('Humaani')
        else:
            game = GameController()
            self.player = GPlayer('Ihiminen')

        self.player.messageReceived.connect(self.append_text)
        self.player.handChanged.connect(self.hand_changed)
        self.player.game_state.stateChanged.connect(self.state_changed)
        self.player.trickPlayed.connect(self.trick_played)
        game.register_player(self.player)

        if remote:
            self.player.start()
            game.start_game_with_bots()
        else:
            for i in range(1, 4):
                if i % 2 == 0:
                    game.register_player(CountingBotPlayer('Lopotti %d' % i))
                else:
                    game.register_player(DummyBotPlayer('Robotti %d' % i))

            game.start_game()

    def card_clicked(self, card):
        #self.append_text("card %s clicked" % unicode(card))
        try:
            self.player.play_a_card(card)
        except common.RuleError, rerror:
            self.append_text("Oops: %s" % str(rerror))

    def hand_changed(self, hand):
        self.draw_hand()

    def append_text(self, text):
        self.text.appendPlainText(text)
        self.text.moveCursor(QTextCursor.End)
        sbar = self.text.verticalScrollBar()
        sbar.setValue(sbar.maximum())

    def state_changed(self, state):
        self.append_text("state_changed(): %s, len(table): %d" % \
                (str(state), len(state.table)))
        print("state_changed(): %s, len(table): %d" % \
                (str(state), len(state.table)))
        self.status_area.setText(str(state))
        self.table.draw_cards(state.table, self.player.id)
        self.draw_hand()

    def trick_played(self, player, state):
        self.append_text("%s takes the trick" % str(player))
        print "table: %s" % str(state.table)
        self.table.draw_cards(state.table, self.player.id)
        # TODO: is there a better way to implement the delay?
        QTimer.singleShot(2000, self.player.event_handled)

    def draw_hand(self):
        for widget in self.hand_widget.findChildren(QWidget):
            widget.deleteLater()

        if self.player.hand is None:
            return

        for card in self.player.hand:
            gcard = GCard(card.suit, card.value, parent=self.hand.parentWidget())
            gcard.clicked.connect(self.card_clicked)
            self.hand.addWidget(gcard)

    def quit_game(self):
        self.player.quit()
        

def main():
    # Every PyQt4 application must create an application object.
    # The application object is located in the QtGui module.
    app = QApplication(sys.argv)

    format = "%(message)s"
    logging.basicConfig(level=logging.INFO, format=format)

    win = TupeloApp()
    win.show()

    ret = app.exec_()
    win.quit_game()

    sys.exit(ret)  # Finally, we enter the mainloop of the application.

if __name__ == '__main__':
    main()
