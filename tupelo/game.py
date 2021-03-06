#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sts=4 sw=4 et:

import threading
import sys
import copy
import logging
from typing import Optional, List

from .common import CardSet, Card
from .common import NOLO, RAMI, DIAMOND, HEART
from .common import TURN_NONE
from .common import RuleError, GameError, GameState
from .common import synchronized_method
from .players import Player, ThreadedPlayer

logger = logging.getLogger()

class GameController():
    """
    The controller class that runs everything.
    """

    def __init__(self):
        super().__init__()
        self.players = []
        self.state = GameState()
        self.shutdown_event = threading.Event()
        self.id = None
        self.lock_start = threading.Lock()

    def register_player(self, player: Player):
        """
        Register a new Player.
        """
        if player.id in [pl.id for pl in self.players]:
            raise GameError('Player already registered to game')

        if len(self.players) == 4:
            raise GameError('Already 4 players registered')

        self.players.append(player)
        # TODO: should we generate UUIDs instead?
        if player.id is None:
            player.id = str(self.players.index(player))

        player.team = self.players.index(player) % 2

    def player_leave(self, player_id: int):
        """
        Player leaves the game.
        """
        self._send_msg('Player %s quit' % player_id)
        plr = self.get_player(player_id)
        if plr:
            self.players.remove(plr)
            plr.hand.clear()
            plr.stop() # stops the thread in case of ThreadedPlayer

        # reset the game unless we are still in OPEN state
        if self.state.status != GameState.OPEN:
            self._reset()

    def player_quit(self, player_id: int):
        """
        Leave and quit the game.
        """
        self.player_leave(player_id)
        self.shutdown_event.set()

    def get_player(self, player_id: int) -> Optional[Player]:
        """
        Get player by id.
        """
        for plr in self.players:
            if plr.id == player_id:
                return plr

        return None

    def _get_player_in_turn(self, turn: int) -> Optional[Player]:
        """
        Get player who is in turn.
        """
        if turn >= 0:
            return self.players[turn % 4]

        return None

    def _next_in_turn(self, thenext: Optional[int] = None):
        """
        Set the next player in turn.
        """
        self.state.next_in_turn(thenext)
        self.state.turn_id = self._get_player_in_turn(self.state.turn).id

    def _set_state(self, new_status: int):
        """
        Change the game state.
        """
        self.state.status = new_status
        for player in self.players:
            player.state_changed(self.state)

    def _stop_players(self):
        """
        Stop all running players.
        """
        self._set_state(GameState.STOPPED)
        for player in self.players:
            if player:
                player.act(self, self.state)

        for player in self.players:
            if player and isinstance(player, ThreadedPlayer):
                if player.is_alive() and player.thread is not threading.current_thread():
                    player.join()

    def _reset(self):
        """
        Reset the game.
        """
        logger.info('Resetting')
        self._stop_players()
        self.players = []
        self.state = GameState()

    def _get_team_players(self, team: int) -> List[Player]:
        """
        Get players in a team.
        """
        return [player for player in self.players if player.team == team]

    def _get_team_str(self, team: int) -> str:
        """
        Get team string representation.
        """
        plrs = self._get_team_players(team)
        return '%d (%s)' % (team + 1, ', '.join([pl.player_name for pl in plrs]))

    def _send_msg(self, msg: str):
        """
        Send a message to all players.
        """
        logger.debug(msg)
        for player in self.players:
            player.send_message('', msg)

    @synchronized_method('lock_start')
    def start_game(self):
        """
        Start the game.
        """
        if self.state.status != GameState.OPEN:
            raise GameError('Game already started')

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

    def _signal_act(self):
        """
        Tell the player who is in turn to act.
        """
        self._get_player_in_turn(self.state.turn).act(self, self.state)

    def _start_new_hand(self):
        """
        Start a new hand.
        """
        logger.info('New hand')
        self.state.tricks = [0, 0]

        # create a full deck
        deck = CardSet.new_full_deck()

        logger.debug('deck is %s', str(deck))
        deck.shuffle()
        logger.debug('shuffled deck %s', str(deck))

        deck.deal([player.hand for player in self.players])

        for player in self.players:
            player.hand.sort()
            logger.debug("%s's hand: %s", player.player_name,
                str(player.hand))

        # voting
        self.state.mode = NOLO
        self.state.rami_chosen_by = None
        self._set_state(GameState.VOTING)

        # uncomment following to skip voting
        #self._set_state(GameState.ONGOING)
        # start the game
        self._next_in_turn(self.state.dealer + 1)
        self._signal_act()

    def _trick_played(self):
        """
        A trick (4 cards) has been played.
        """
        table = self.state.table
        high = table.get_cards(suit=table[0].suit).get_highest()
        high_played_by = self.get_player(high.played_by)
        team = high_played_by.team
        self._send_msg('Team %s takes this trick' % (self._get_team_str(team)))
        self.state.tricks[team] += 1
        self._send_msg('Tricks: %s' % self.state.tricks)
        # send signals
        for plr in self.players:
            plr.trick_played(high_played_by, self.state)

        self.state.table.clear()

        # do we have a winner?
        if self.state.tricks[0] + self.state.tricks[1] == 13:
            self._hand_played()
        else:
            self._next_in_turn(self.players.index(high_played_by))
            self._signal_act()

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
            if self.state.rami_chosen_by and self.state.rami_chosen_by.team != winner:
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
        self._stop_players()
        sys.exit(0)

    def _vote_card(self, player: Player, card: Card):
        """
        Player votes with a card.
        """
        table = self.state.table

        card = copy.copy(card)
        card.played_by = player.id
        table.append(card)
        # fire signals
        for plr in self.players:
            plr.card_played(player, card, self.state)

        if card.suit == DIAMOND or card.suit == HEART:
            self.state.mode = RAMI
            self.state.rami_chosen_by = player
            self._next_in_turn(self.players.index(player) - 1)
            self._begin_game()
        elif len(table) == 4:
            self.state.mode = NOLO
            self._next_in_turn()
            self._begin_game()
        else:
            self._next_in_turn()

        self._signal_act()

    def _begin_game(self):
        if self.state.mode == RAMI:
            self._send_msg('Rami it is')
        else:
            self._send_msg('Nolo it is')

        self._send_msg('Game on, %s begins!' % self._get_player_in_turn(self.state.turn))

        self.state.table.clear()
        self._set_state(GameState.ONGOING)

    def play_card(self, player: Player, card: Card):
        """
        Play one card on the table.
        """
        if self._get_player_in_turn(self.state.turn).id != player.id:
            raise RuleError('Not your turn')

        table = self.state.table

        if self.state.status == GameState.VOTING:
            self._vote_card(player, card)

        elif self.state.status == GameState.ONGOING:
            # make sure that suit is followed
            if len(table) > 0 and card.suit != table[0].suit:
                if len(player.hand.get_cards(suit=table[0].suit)) > 0:
                    raise RuleError('Suit must be followed')

            # make sure that the player actually has the card
            try:
                table.append(player.hand.take(card))
                card.played_by = player.id
            except ValueError:
                raise RuleError('Invalid card')

            if len(table) == 4:
                # TODO: there must be a better way for this
                turn_backup = self.state.turn
                self.state.turn = TURN_NONE
                # fire signals with temporary state
                # this is to let clients know that all four cards have been played
                # and it's nobody's turn yet
                for plr in self.players:
                    plr.card_played(player, card, self.state)

                self.state.turn = turn_backup
                self._trick_played()
            else:
                self._next_in_turn()
                # fire signals
                for plr in self.players:
                    plr.card_played(player, card, self.state)
                self._signal_act()

