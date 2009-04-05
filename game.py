#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import common
from common import CardSet
from common import NOLO, RAMI
from common import STOPPED, VOTING, ONGOING
from common import RuleError, GameError, GameState 
from players import DummyBotPlayer, CountingBotPlayer, CliPlayer
import threading
import sys
import copy

class GameController(object):
    """
    The controller class that runs everything.
    """

    def __init__(self):
        self.players = []
        self.state = GameState()
        self.shutdown_event = threading.Event()

    def register_player(self, player):
        """
        Register a new Player.
        """
        if len(self.players) == 4:
            raise GameError('Already 4 players registered')

        self.players.append(player)
        player.id = self.players.index(player)
        player.team = player.id % 2

    def _get_team_players(self, team):
        """
        Get players in a team.
        """
        return [player for player in self.players if player.team == team]
       
    def _get_team_str(self, team):
        """
        Get team string representation.
        """
        players = self._get_team_players(team)
        return '%d (%s and %s)' % (team + 1, players[0].player_name, players[1].player_name)

    def _send_msg(self, msg):
        """
        Send a message to all players.
        """
        print msg
        for player in self.players:
            player.send_message('', msg)

    def start_game(self):
        """
        Start the game.
        """
        if len(self.players) < 4:
            raise GameError('Not enough players')
        
        for player in self.players:
            player.start()

        self._start_new_hand()

    def wait_for_shutdown(self):
        """
        Wait for shutdown event and shut down after it.
        """
        self.shutdown_event.wait()
        self.shutdown()
            
    def _start_new_hand(self):
        """
        Start a new hand.
        """
        print 'New hand'
        self.state.tricks = [0, 0]

        # create a full deck
        deck = CardSet.new_full_deck()

        #print 'deck is', deck
        deck.shuffle()
        #print 'shuffled deck', deck

        deck.deal([player.hand for player in self.players])

        for player in self.players:
            player.hand.sort()
            print "%s's hand " % player.player_name, player.hand

        # voting 
        self.state.mode = NOLO
        self.state.rami_chosen_by = None
        self.state.state = VOTING

        # uncomment following to skip voting
        #self.state.state = ONGOING
        # start the game
        self.state.next_in_turn(self.state.dealer + 1)
        self.players[self.state.turn].act(self, self.state)

    def _trick_played(self):
        """
        A trick (4 cards) has been played.
        """
        table = self.state.table
        high = table.get_cards(suit=table[0].suit).get_highest()
        team = high.played_by.team
        self._send_msg('Team %s takes this trick' % (self._get_team_str(team)))
        self.state.tricks[team] += 1
        self._send_msg('Tricks: %s' % self.state.tricks)
        self.state.table.clear()

        # do we have a winner?
        if self.state.tricks[0] + self.state.tricks[1] == 13:
            self._hand_played()
        else:
            self.state.next_in_turn(high.played_by.id)
            self.players[self.state.turn].act(self, self.state)

    def _hand_played(self):
        """
        A hand has been played.
        """

        if self.state.mode == NOLO:
            if self.state.tricks[0] < self.state.tricks[1]:
                winner = 0
                loser = 1
            else:
                winner = 1
                loser = 0
            score = (7 - self.state.tricks[winner]) * 4
        else: 
            if self.state.tricks[0] > self.state.tricks[1]:
                winner = 0
                loser = 1
            else:
                winner = 1
                loser = 0
            if self.state.rami_chosen_by.team != winner:
                self._send_msg("Double points for taking opponent's rami!")
                score = (self.state.tricks[winner] - 6) * 8
            else:
                score = (self.state.tricks[winner] - 6) * 4

        self._send_msg('Team %s won this hand with %d tricks' % 
                (self._get_team_str(winner), self.state.tricks[winner]))

        if self.state.score[loser] > 0:
            self._send_msg('Team %s fell down' % (self._get_team_str(loser)))
            self.state.score = [0, 0]
        else:
            self.state.score[winner] += score
            if self.state.score[winner] > 52:
                self._send_msg('Team %s won with score %d!' % 
                        (self._get_team_str(winner), self.state.score[winner]))
                self.shutdown_event.set()
                return
            else:
                self._send_msg('Team %s is at %d' % 
                        (self._get_team_str(winner), self.state.score[winner]))

        self.state.dealer = (self.state.dealer + 1) % 4
        self._start_new_hand()

    def shutdown(self):
        """
        Shutdown the game.
        """
        self.state.state = STOPPED
        for player in self.players:
            player.act(self, self.state)

        for player in self.players:
            if player.isAlive():
                player.join()

        sys.exit(0)

    def _vote_card(self, player, card):
        """
        Player votes with a card.
        """
        table = self.state.table

        card = copy.copy(card)
        card.played_by = player
        table.append(card)
        self.state.next_in_turn()
        if len(table) == 4:
            for card in table:
                # fire signals
                for plr in self.players:
                    plr.card_played(card.played_by, card, self.state)
                if card.suit == common.DIAMOND or card.suit == common.HEART:
                    self.state.mode = RAMI
                    self.state.rami_chosen_by = player
                    self.state.next_in_turn(card.played_by.id - 1)
                    break
            table.clear()
            if self.state.mode == NOLO:
                self._send_msg('Nolo it is')
            else:
                self._send_msg('Rami it is')
            self.state.state = ONGOING
            self._send_msg('Game on, %s begins!' % self.players[self.state.turn])

        self.players[self.state.turn].act(self, self.state)
            
    def play_card(self, player, card):
        """
        Play one card on the table.
        """
        if self.state.turn != player.id:
            raise RuleError('Not your turn')

        table = self.state.table

        if self.state.state == VOTING:
            self._vote_card(player, card)

        elif self.state.state == ONGOING:
            # make sure that suit is followed
            if len(table) > 0 and card.suit != table[0].suit:
                if len(player.hand.get_cards(suit=table[0].suit)) > 0:
                    raise RuleError('Suit must be followed')
            
            # make sure that the player actually has the card
            try: 
                table.append(player.hand.take(card))
                card.played_by = player
            except ValueError:
                raise RuleError('Invalid card')

            # fire signals
            for plr in self.players:
                plr.card_played(player, card, self.state)

            if len(table) == 4:
                self._trick_played()
            else:
                self.state.next_in_turn()
                self.players[self.state.turn].act(self, self.state)
        
if __name__ == '__main__':

    game = GameController()

    #game.register_player(CliPlayer('Ihminen'))
    for i in range(0, 4):
        if i % 2 == 0:
            game.register_player(CountingBotPlayer('Lopotti %d' % i))
        else:
            game.register_player(DummyBotPlayer('Robotti %d' % i))

    game.start_game()
    game.wait_for_shutdown()