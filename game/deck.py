from random import shuffle
from collections import defaultdict


# Return a new card (ace of spades by default)
def new_card(suit=0, value=14):
    return {'suit': suit, 'value': value}


# Return string representation of a suit
def suit_to_string(suit):
    suits = {
        0: 'Spades',
        1: 'Hearts',
        2: 'Diamonds',
        3: 'Clubs'
    }
    return suits[suit]


# Return a string representing the card
def card_to_string(card):
    values = {
        11: 'Jack',
        12: 'Queen',
        13: 'King',
        14: 'Ace'
    }
    values = defaultdict(lambda: card['value'], values)

    return str(values[card['value']]) + ' of ' + suit_to_string(card['suit'])


# Return a new deck (empty & unshuffled by default)
def new_deck(filled=False, shuffled=False):
    deck = {'cards': []}
    if filled:
        fill_deck(deck, shuffled=shuffled)

    if shuffled:
        shuffle(deck['cards'])

    return deck


# Fill a deck with one of every card
def fill_deck(deck, shuffled=False):
    for suit in range(4):
        for value in range(2, 15):
            deck['cards'].append(new_card(suit, value))


# Add specified card to front of deck
def push_front(deck, card):
    deck['cards'].insert(0, card)


# Add specified card to end deck
def push_back(deck, card):
    deck['cards'].append(card)


# Remove card from beginning of deck
def pop_back(deck):
    return deck['cards'].pop()


# Remove and return card at index
def remove_card(deck, index):
    card = deck['cards'][index]
    del deck['cards'][index]
    return card


# Copy all the cards from the middle to the trick-taker's pile
def collect_trick(game):
    # Take one card for each player in the game
    for card in range(game['num_players']):
        push_back(game['tricks'][game['players'][game['taker']]], pop_back(game['middle_cards']))


# Sort deck (trump, then lead, then others)
def sort_deck(deck, game):
    # Create list of empty lists, one for each suit
    suit_lists = [[] for suit in range(4)]

    # Put cards in list for their suit
    for card in deck['cards']:
        suit_lists[card['suit']].append(card)

    # Empty deck
    deck['cards'].clear()

    # For each suit list
    for suit in range(4):
        # Sort suit list by card values (descending)
        suit_lists[suit].sort(key=lambda card: card['value'], reverse=True)

    # Make sure trump comes first
    deck['cards'] += suit_lists[game['trump']]

    # Only add lead cards if lead != trump
    if game['lead_suit'] != game['trump']:
        deck['cards'] += suit_lists[game['lead_suit']]

    # Add all other cards back to the deck
    for suit in range(4):
        if suit != game['trump'] and suit != game['lead_suit']:
            deck['cards'] += suit_lists[suit]


# Return number of playable cards in the hand
def playable_cards(game, player):
    # No one's turn yet, no cards playable
    if game['turn'] == -1:
        return 0

    # If player is the active player
    if player == game['players'][game['active_player']]:
        # If first turn, any card is playable
        if game['turn'] == 0:
            return game['hand_size']

        num_trump = 0
        num_lead = 0

        # Count number of trump and lead suit cards
        for card in game['hands'][player]['cards']:
            if card['suit'] == game['lead_suit']:
                num_lead += 1
            elif card['suit'] == game['trump']:
                num_trump += 1

        # If no lead suit cards
        if num_lead == 0:
            # Can play anything (trump or other)
            return len(game['hands'][player]['cards'])
        else:
            return num_trump + num_lead
    else:
        return 0
