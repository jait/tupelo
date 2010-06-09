#!/usr/bin/env python
# vim: set sts=4 sw=4 et:
# -*- coding: utf-8 -*-
#
import sys
from PyQt4.QtGui import *
from qcommon import QCard, GPlayer
import common
import logging
from game import GameController
from players import DummyBotPlayer, CountingBotPlayer


class TupeloApp(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.resize(640, 480)
        self.setWindowTitle("Tupelo")
        hbox = QHBoxLayout(self)

        self.hand_widget = QWidget()
        self.hand = None
        self.hand = QHBoxLayout(self.hand_widget)

        hbox.addWidget(self.hand_widget)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        hbox.addWidget(self.text)
        self.game = self.create_game()
        self.draw_hand()
       
    def create_game(self):
        game = GameController()

        self.player = GPlayer('Ihiminen')

        self.player.messageReceived.connect(self.text.appendPlainText)
        self.player.handChanged.connect(self.hand_changed)
        game.register_player(self.player)

        for i in range(1, 4):
            if i % 2 == 0:
                game.register_player(CountingBotPlayer('Lopotti %d' % i))
            else:
                game.register_player(DummyBotPlayer('Robotti %d' % i))

        game.start_game()
        return game

    def card_clicked(self, card):
        self.text.appendPlainText("card %s clicked" % unicode(card))
        try:
            self.player.play_a_card(card)
        except common.RuleError, rerror:
            self.text.appendPlainText("Oops: %s" % str(rerror))

    def hand_changed(self, hand):
        self.draw_hand()

    def draw_hand(self):
        # TODO: doesn't work
        for widget in self.hand_widget.findChildren(QWidget):
            del widget

        #self.hand = QHBoxLayout(self.hand_widget)
        for card in self.player.hand:
            gcard = QCard(card.suit, card.value, parent=self.hand.parentWidget())
            gcard.clicked.connect(self.card_clicked)
            self.hand.addWidget(gcard)

    def quit_game(self):
        self.game.player_quit(self.player.id)
        
            
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

