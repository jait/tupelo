#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import threading
from .common import CardSet, SPADE, CLUB, HEART, DIAMOND
from .common import NOLO, RAMI
from .common import RuleError, UserQuit, GameState
from . import rpc

class Player(rpc.RPCSerializable):
    """
    Base class for players.
    """
    rpc_attrs = ('id', 'player_name', 'team')

    def __init__(self, name):
        self.id = None
        rpc.RPCSerializable.__init__(self)
        self.player_name = name
        self.hand = CardSet()
        self.team = 0
        self.controller = None
        self.game_state = GameState()

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.player_name)

    def __getstate__(self):
        """
        Make Player classes safe for pickling and deepcopying.
        """
        state = {}
        for key, _ in self.iter_rpc_attrs():
            state[key] = getattr(self, key)

        return state

    @classmethod
    def rpc_decode(cls, rpcobj):
        """
        Decode an RPC-form object into an instance of cls.
        """
        player = cls(rpcobj['player_name'])
        for attr, atype in cls.iter_rpc_attrs():
            if attr != 'player_name':
                player.rpc_decode_attr(rpcobj, attr, atype)

        return player

    def start(self):
        """
        Start the player.
        """
        pass

    def stop(self):
        """
        Stop the player.
        """
        pass

    def card_played(self, player, card, game_state):
        """
        Signal that a card has been played by the given player.
        """
        pass

    def trick_played(self, player, game_state):
        """
        Signal that a trick has been played. "player" had the winning card.
        """
        pass

    def state_changed(self, game_state):
        """
        Signal that the game state has changed, e.g. from VOTING to ONGOING.
        """
        pass

    def vote(self):
        """
        Vote for rami or nolo.
        """
        print('Not implemented!')
        raise NotImplementedError()

    def play_card(self):
        """
        Play one card.
        """
        print('Not implemented!')
        raise NotImplementedError()

    def send_message(self, sender, msg):
        """
        """
        print('Not implemented!')
        raise NotImplementedError()

    def act(self, controller, game_state):
        """
        Do something.

        This is an event handler that updates
        the game state and wakes up the thread.
        """
        print('Not implemented!')
        raise NotImplementedError()


class ThreadedPlayer(Player):

    def __init__(self, name):
        Player.__init__(self, name)
        self.thread = self._create_thread()
        self.turn_event = threading.Event()
        self.stop_flag = False

    def _create_thread(self):
        """
        Create a new thread for this player.
        """
        try:
            strname = str(self.player_name)
        except UnicodeEncodeError:
            strname = [x for x in self.player_name if ord(x) < 128]

        return threading.Thread(None, self.run, strname)

    def wait_for_turn(self):
        """
        Wait for this player's turn.
        """
        #print "%s waiting for my turn" % self
        self.turn_event.wait()
        #print "%s it's about time!" % self
        self.turn_event.clear()

    def is_alive(self):
        """
        Return true if the player thread is alive.
        """
        if self.thread is not None:
            return self.thread.isAlive()

        return False

    def start(self):
        """
        (Re)start the player thread.
        """
        if self.thread is None:
            self.thread = self._create_thread()

        # try to handle restart attempts
        try:
            return self.thread.start()
        except RuntimeError:
            # if the thread is still running, the exception is valid
            if self.is_alive():
                raise

            self.thread = self._create_thread()
            return self.thread.start()

    def join(self, timeout=5.0):
        """
        Join the player thread, if one exists.
        """
        if self.thread is None:
            return

        return self.thread.join(timeout)

    def run(self):
        """
        The real work is here.
        """
        print(('%s starting' % self))
        self.stop_flag = False
        while True:

            self.wait_for_turn()

            if self.game_state.state == GameState.STOPPED or \
                    self.stop_flag == True:
                break
            elif self.game_state.state == GameState.VOTING:
                try:
                    self.vote()
                except UserQuit as error:
                    print(('UserQuit:', error))
                    self.controller.player_quit(self.id)
                    break
                except Exception as error:
                    print(('Error:', error))
                    raise
            elif self.game_state.state == GameState.ONGOING:
                try:
                    self.play_card()
                except UserQuit as error:
                    print(('UserQuit:', error))
                    self.controller.player_quit(self.id)
                    break
                except Exception as error:
                    print(('Error:', error))
                    raise
            else:
                print(("Warning: unknown state %d" % self.game_state.state))

        print(('%s exiting' % self))

    def stop(self):
        """
        Try to stop the thread, regardless of the state.
        """
        self.stop_flag = True
        self.turn_event.set()

    def act(self, controller, game_state):
        """
        Do something.

        This is an event handler that updates
        the game state and wakes up the thread.
        """
        self.controller = controller
        self.game_state.update(game_state)
        self.turn_event.set()

class DummyBotPlayer(ThreadedPlayer):
    """
    Dummy robot player.
    """

    def send_message(self, sender, msg):
        """
        Robots don't care about messages.
        """
        pass

    def vote(self):
        """
        Vote for rami or nolo.
        """
        # simple algorithm
        score = 0
        for card in self.hand:
            if card.value > 10:
                score += card.value - 10

        if score > 16:
            # rami, red cards
            choices = self.hand.get_cards(suit=HEART)
            choices.extend(self.hand.get_cards(suit=DIAMOND))
        else:
            # nolo, black cards
            choices = self.hand.get_cards(suit=SPADE)
            choices.extend(self.hand.get_cards(suit=CLUB))
            
        if len(choices) == 0:
            choices = self.hand

        best = None
        for card in choices:
            if best is None or abs(6 - card.value) < abs(6 - best.value):
                best = card

        try:
            #print '%s voting %s' % (self, best)
            self.controller.play_card(self, best)
        except RuleError as error:
            print('Oops', error)
            raise

    def play_card(self):
        state = self.game_state

        # pick a card, how hard can it be?
        card = None
        if len(state.table) == 0:
            choices = self.hand
        else:
            choices = self.hand.get_cards(suit=state.table[0].suit)

        if state.mode == NOLO:
            if len(choices) == 0:
                # "sakaus"
                # should be "worst score"
                card = self.hand.get_highest()
            else:
                # real dumb
                card = choices.get_lowest()
                if len(state.table) > 0:
                    high = state.table.get_cards(suit=state.table[0].suit).get_highest()
                    high_played_by = self.controller.get_player(high.played_by)
                    if high_played_by.team == self.team:
                        # we may be getting this trick...
                        if len(state.table) == 3:
                            # and i'm the last to play
                            card = choices.get_highest()
                        else:
                            # i'm third
                            # TODO: should also consider higher cards 
                            candidate = choices.get_highest(roof=high.value)
                            if candidate is not None:
                                card = candidate
                            else:
                                # might have to take this one
                                card = choices.get_highest()
                    else:
                        # the opponent may get this trick, play under
                        candidate = choices.get_highest(roof=high.value)
                        if candidate is not None:
                            card = candidate
                        else:
                            # cannot go under...
                            if len(state.table) == 3:
                                # and i'm the last to play
                                card = choices.get_highest()
                            else:
                                pass

        elif state.mode == RAMI:
            if len(choices) == 0:
                # should be "worst score" or "least value"
                card = self.hand.get_lowest()
            else:
                # real dumb
                card = choices.get_highest()
                if len(state.table) > 0:
                    high = state.table.get_cards(suit=state.table[0].suit).get_highest()
                    high_played_by = self.controller.get_player(high.played_by)
                    if high_played_by.team == self.team:
                        # we may be getting this trick...
                        card = choices.get_lowest()
                    else:
                        if len(state.table) == 3:
                            # i'm the last to play
                            # take it as cheap as possible, if possible
                            candidate = choices.get_lowest(floor=high.value)
                            if candidate is not None:
                                card = candidate
                            else:
                                card = choices.get_lowest()
                        else:
                            # i'm second or third
                            candidate = choices.get_highest(floor=high.value)
                            if candidate is not None:
                                card = candidate
                            else: 
                                # but I cannot take it...
                                card = choices.get_lowest()
                                
        try:
            #print '%s playing %s' % (self, card)
            self.controller.play_card(self, card)
        except RuleError as error:
            print('Oops', error)
            raise


class CountingBotPlayer(DummyBotPlayer):
    """
    Robot player that counts played cards.
    """

    def __init__(self, name):
        DummyBotPlayer.__init__(self, name)
        self.cards_left = CardSet()

    def vote(self):
        """
        Vote for rami or nolo.
        """
        self.cards_left = CardSet.new_full_deck() - self.hand
        super(CountingBotPlayer, self).vote()

    def card_played(self, player, card, game_state):
        """
        Signal that a card has been played by the given player.
        """
        if player == self:
            return

        if game_state.state == GameState.VOTING:
            pass
        elif game_state.state == GameState.ONGOING:
            #print "removing %s  from %s" %(card, self.cards_left)
            try:
                self.cards_left.remove(card)
            except ValueError:
                print("Oops: removing card %s failed" % card)
                # TODO: we sometimes get this with CountingBotPlayer


class CliPlayer(ThreadedPlayer):
    """
    Command line interface human player.
    """

    def _pick_card(self, prompt='Pick a card'):
        """
        Pick one card from the player's hand.
        """
        print('Your hand:')
        print('  '.join('%3s' % (card) for card in self.hand))
        for i in range(0, len(self.hand)):
            print('%3d ' % (i + 1), end=' ')
        print()

        card_ok = False
        card = None
        while not card_ok:
            try:
                uinput = input('%s (1-%d) --> ' % (prompt, len(self.hand)))
                index = int(uinput) - 1
                if index < 0:
                    raise IndexError()
                card = self.hand[index] 
                card_ok = True
            except (IndexError, ValueError):
                print("Invalid choice `%s'" % uinput)
            except EOFError:
                #error.message = 'EOF received from command line'
                #error.args = error.message,
                #raise error
                raise EOFError('EOF received from command line')

        return card

    def vote(self):
        """
        Vote for rami or nolo.
        """
        print('Voting')
        card_played = False
        while not card_played:
            try:
                card = self._pick_card()
                print('Voting with %s' % (card))
                self.controller.play_card(self, card)
                card_played = True
            except RuleError as error:
                print('Oops:', error)
            except EOFError:
                raise UserQuit('EOF from command line')

    def play_card(self):
        """
        Play one card.
        """
        state = self.game_state

        # print table
        if state.mode == NOLO:
            print('Playing nolo')
        elif state.mode == RAMI:
            print('Playing rami')
        else:
            print('Unknown mode %d' % state.mode)

        print('Table:')
        for card in state.table:
            try:
                plr = '%s: ' % self.controller.get_player(card.played_by).player_name
            except:
                # showing the (random) player ID is not very intuitive
                plr = ''
            print('%s%s' % (plr, card))

        card_played = False
        while not card_played:
            try:
                card = self._pick_card('Card to play')
                print('Playing %s' % (card))
                self.controller.play_card(self, card)
                card_played = True
            except RuleError as error:
                print('Oops:', error)
            except EOFError:
                raise UserQuit('EOF from command line')

    def card_played(self, player, card, game_state):
        """
        Event handler for a played card.
        """
        if player.id == self.id:
            player_str = 'You'
        else:
            player_str = '%s' % player

        if game_state.state == GameState.VOTING:
            print('%s voted %s' % (player_str, card))
        else:
            print('%s played %s' % (player_str, card))

    def send_message(self, sender, msg):
        """
        Send a message to this player.
        """
        if sender is not None:
            print('%s: %s' % (sender, msg))
        else:
            print('%s' % msg)

