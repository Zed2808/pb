from random import shuffle

# Return a new card (ace of spades by default)
def new_card(suit=0, value=14):
	return {'suit': suit, 'value': value}

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

# Add specified card to end deck
def push_back(deck, card):
	deck['cards'].append(new_card(card['suit'], card['value']))

# Remove card from beginning of deck
def pop_back(deck):
	return deck['cards'].pop()

# Sort deck (trump, then lead, then others)
def sort_deck(deck, trump, lead):
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
	deck['cards'] += suit_lists[trump]

	# Only add lead cards if lead != trump
	if lead != trump:
		deck['cards'] += suit_lists[lead]

	# Add all other cards back to the deck
	for suit in range(4):
		if suit != trump and suit != lead:
			deck['cards'] += suit_lists[suit]
