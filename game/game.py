from flask import request
from collections import defaultdict
import random, string
from .deck import *
from .html import *
from .pb import *

# Initialize the gamestate and add it to the list of games, return the created game
def create_new_game(games, game_id):
	game = {
		'id': game_id,
		'players': [],
		'num_players': 2,
		'hand_size': 6,
		'dealer': 0,
		'active_player': 1,
		'min_bid': 2,
		'bid': 0,
		'bidder': -1,
		'round': -1,
		'round_over': False,
		'turn': -1,
		'taker': -1,
		'played_card': new_card(),
		'top_card': new_card(),
		'trump': 0,
		'trump_set': False,
		'lead_suit': 0,
		'deck': new_deck(filled=True, shuffled=True),
		'middle_cards': new_deck(),
		'hands': {},
		'hands_dealt': False,
		'tricks': {},
		'scores': {},
		'score_limit': 11
	}

	# Set empty returns
	reset_returns(game)

	# Append newly created game to list of games
	games.append(game)

	return game

# Add new player to game
def add_player(game, username):
	# Add player to this game's players by username
	game['players'].append(username);

	# Create hand, trick pile, and score for new player
	game['hands'][username] = new_deck()
	game['tricks'][username] = new_deck()
	game['scores'][username] = 0

# Generate new 4 letter game ID
def new_game_id():
	game_id = ''
	for x in range(4):
		game_id += random.choice(string.ascii_uppercase)

	return game_id

# Generate new generic username (player + 5 random numbers)
def new_username():
	return 'Player{}'.format(random.randint(10000, 100000))

# Return game given its game ID
def get_game(games, game_id):
	game = [game for game in games if game['id'] == game_id]
	if len(game) == 0:
		return None
	return game[0]

# Advance active_player, looping if necessary
def advance_player(game):
	game['active_player'] += 1
	if game['active_player'] >= game['num_players']:
		game['active_player'] = 0

# Advance to next dealer, looping if necessary
def advance_dealer(game):
	game['dealer'] += 1
	if game['dealer'] >= game['num_players']:
		game['dealer'] = 0

# Find index of next player, looping if necessary
def next_player(game, player):
	index = game['players'].index(player)
	index += 1
	if index >= game['num_players']:
		index = 0
	return game['players'][index]

# Reset HTML return strings
def reset_returns(game):
	game['top_name'] = ''
	game['top_hand'] = ''
	game['middle'] = ''
	game['bottom_hand'] = ''
	game['bottom_name'] = ''
	game['bottom'] = ''
	game['log'] = ''

# Deal hands to players
def deal_hands(game):
	# Re-make the deck before dealing new hands
	game['deck'] = new_deck(filled=True, shuffled=True)

	# Deal hand to each player
	print('>>> Dealing hands to game {}'.format(game['id']))
	for player in game['players']:
		# Deal cards up to hand_size
		for n in range(game['hand_size']):
			# Get card from the deck
			card = pop_back(game['deck'])

			# Add card to player's hand
			push_back(game['hands'][player], card)

	game['log'] += '<p><b>{}</b> bids first.</p>'.format(game['players'][game['active_player']])
	game['hands_dealt'] = True

# Perform a turn of the bidding round
def bidding_round(game, bid):
	# As long as we haven't reached the dealer yet
	if game['active_player'] != game['dealer']:
		# Player's bid
		current_bid = bid

		# Not pass
		if current_bid != 0:
			# Set bid, bidder, new min_bid
			game['bid'] = current_bid
			game['min_bid'] = current_bid + 1
			game['bidder'] = game['active_player']
			print('>>> {} bid {} (game {})'.format(game['players'][game['active_player']], current_bid, game['id']))
			game['log'] = '<p><b>Player {}</b> bid {}.</p>'.format(game['players'][game['bidder']], current_bid)
		# Pass
		else:
			print('>>> {} passes (game {})'.format(game['players'][game['active_player']], game['id']))
			game['log'] = '<p><b>{}</b> passes.</p>'.format(game['players'][game['active_player']])

		# Prepare for next player
		advance_player(game)

		# Check if dealer's hand is forced
		if game['active_player'] == game['dealer'] and game['bid'] < 2:
			game['bid'] = game['min_bid']
			game['bidder'] = game['active_player']

			print('>>> {} is forced to bid {} (game {})'.format(game['players'][game['active_player']], game['bid'], game['id']))

			game['log'] += '<p><b>{}</b> is forced to bid {}.</p>'.format(game['players'][game['bidder']], game['bid'])

			#Prepare for first round
			game['round'] = 0

	# If others have bid, dealer can still match or pass
	else:
		# Player's bid
		current_bid = bid

		# Dealer passes
		if bid == 0:
			game['log'] = '<p><b>{}</b> passes.</p>'.format(game['players'][game['active_player']])
		# Dealer matches
		else:
			game['log'] = '<p><b>{}</b> matches <b>{}</b>\'s bid of {}.</p>'.format(game['players'][game['active_player']],
				                                                                    game['players'][game['bidder']],
				                                                                    game['bid'])
			game['bidder'] = game['active_player']

		#Prepare for first round
		game['round'] = 0

	# If bidding round is over
	if game['round'] == 0:
		print('>>> {} won with a bid of {} (game {})'.format(game['players'][game['bidder']], game['bid'], game['id']))
		game['log'] += '<p><b>{}</b> won with a bid of {}.</p>'.format(game['players'][game['bidder']], game['bid'])

		game['active_player'] = game['bidder']
		game['turn'] = 0

# Play a card
def play_card(game, card_number):
	# Set played card from player's choice
	played_card = remove_card(game['hands'][game['players'][game['active_player']]], card_number)
	print('>>> {} played the {}.'.format(game['players'][game['active_player']], card_to_string(played_card)))

	# Log player's choice
	game['log'] = '<p><b>{}</b> played the {}.</p>'.format(game['players'][game['active_player']], card_to_string(played_card))

	# If leading the round
	if game['turn'] == 0:
		print('>>> {} leads the hand'.format(game['players'][game['active_player']]))

		# Set lead suit, initial taker, top card
		game['lead_suit'] = played_card['suit']
		game['taker'] = game['active_player']
		game['top_card'] = played_card

		# Set trump if first round
		if game['round'] == 0:
			print('>>> {} sets trump as {}'.format(game['players'][game['active_player']], suit_to_string(played_card['suit'])))
			game['trump'] = played_card['suit']
			game['trump_set'] = True
			game['log'] += '<p>Trump is now <b>{}</b>.</p>'.format(suit_to_string(played_card['suit']))
	# Otherwise, check if card beats top
	else:
		if new_top(game, played_card):
			game['top_card'] = played_card
			game['taker'] = game['active_player']

	# Move played card to middle, prepare to display
	push_back(game['middle_cards'], played_card)

	# End player's turn
	advance_player(game)
	game['turn'] += 1

# Check if given card beats the game's current top card
def new_top(game, card):
	# Current top is trump
	if game['top_card']['suit'] == game['trump']:
		# Played card is also trump
		if card['suit'] == game['trump']:
			# Played card value beats top value
			if card['value'] > game['top_card']['value']:
				return True
	# Current top is not trump
	else:
		# Played card is trump
		if card['suit'] == game['trump']:
			return True
		# Played card is lead suit
		elif card['suit'] == game['lead_suit']:
			# Played card value beats top value
			if card['value'] > game['top_card']['value']:
				return True

	# Played card does not beat current top
	return False

# End the round, score hands and prepare for new hand if necessary
def end_round(game):
	# Taker collects trick
	collect_trick(game)
	print('>>> {} takes the trick'.format(game['players'][game['taker']]))

	game['round'] += 1
	print('>>> Advancing to round {}'.format(game['round']))
	game['turn'] = -1
	game['active_player'] = game['taker']

	# Last round of the hand
	if game['round'] >= game['hand_size']:
		# Score hands
		print('>>> Scoring hands')
		game['log'] += score_hands(game)

		# Prepare for a new hand
		game['hands_dealt'] = False
		game['trump_set'] = False
		game['round'] = -1
		advance_dealer(game)
		game['active_player'] = game['dealer']
		advance_player(game)
		game['min_bid'] = 2
		game['bid'] = 0
		game['bidder'] = -1

# Score hands and modify game state
def score_hands(game):
	high_trump = 1
	low_trump = 15
	jack_taker = -1
	game_taker = -1
	hand_scores = []
	pips = []

	pip_values = {
		10: 10,
		11: 1,
		12: 2,
		13: 3,
		14: 4
	}
	pip_values = defaultdict(lambda: 0, pip_values)

	# For each stack of tricks
	for player in range(game['num_players']):
		# Append a 0 to hand_scores and pips for each player
		hand_scores.append(0)
		pips.append(0)

		# For each card in the trick stack
		for card in game['tricks'][player]['cards']:
			# If card is trump
			if card['suit'] == game['trump']:
				# If card is higher than current high trump
				if card['value'] > high_trump:
					high_trump = card['value']
					high_taker = player

				# If card is lower than current low trump
				if card['value'] < low_trump:
					low_trump = card['value']
					low_taker = player

				# If card is jack
				if card['value'] == 11:
					jack_taker = player

			# Add pips
			pips[player] += pip_values[card['value']]

		print('>>> player {} game points: {}'.format(player, pips[player]))

	# Find game point taker
	max_pips = 0
	for player in range(game['num_players']):
		if pips[player] > max_pips:
			game_taker = player
			max_pips = pips[player]
		# Tie: set taker to -1
		elif pips[player] == max_pips:
			game_taker = -1

	# Add up hand scores
	hand_scores[high_taker] += 1
	hand_scores[low_taker] += 1
	if jack_taker > -1:
		hand_scores[jack_taker] += 1
	if game_taker > -1:
		hand_scores[game_taker] += 1

	# Return log message
	msg = '<p><b>Player {}</b> took high.</p>'.format(high_taker + 1)
	msg += '<p><b>Player {}</b> took low.</p>'.format(low_taker + 1)
	if jack_taker > -1:
		msg += '<p><b>Player {}</b> took jack.</p>'.format(jack_taker + 1)
	if game_taker > -1:
		msg += '<p><b>Player {}</b> took game.</p>'.format(game_taker + 1)
	else:
		msg += '<p>Players tied for game.</p>'

	for player in range(game['num_players']):
		# If player was the bidder
		if player == game['bidder']:
			# If bidder does not make their bid
			if hand_scores[player] < game['bid']:
				# Set hand score to -bid
				hand_scores[game['bidder']] = -(game['bid'])
				msg += '<p><b>Player {0}</b> did not make their bid of {1} and loses {1} points.</p>'.format(player+1, game['bid'])
			# Bidder did make their bid
			else:
				msg += '<p><b>Player {}</b> made their bid of {} and gets {} points.</p>'.format(player+1, game['bid'], hand_scores[player])
		# Player was not the bidder
		elif hand_scores[player] > 0:
			msg += '<p><b>Player {}</b> gets {} points.</p>'.format(player+1, hand_scores[player])

	# Add hand scores to game scores
	for player in range(game['num_players']):
		game['scores'][player] += hand_scores[player]

	return msg

# Prepare hands for display
def prepare_hands(game, client):
	# Hands ready for display
	hands = {}

	# Prepare each player's hand
	for player in game['players']:
		# If preparing client's hand
		if player == client:
			# Create entry for player
			hands[player] = ''

			# Sort player's hand
			sort_deck(game['hands'][player], game)

			# Get number of playable cards
			playable = playable_cards(game, player)

			# Add card HTML to display for each card in player's hand
			for n in range(len(game['hands'][player]['cards'])):
				# Get card n
				card = game['hands'][player]['cards'][n]

				# If card is playable, make it clickable
				if n in range(playable):
					# If card is trump and trump has been set
					if card['suit'] == game['trump'] and game['trump_set']:
						card_class = 'trump'
					else:
						card_class = ''

					hands[player] += card_clickable_html.format(card_class, n, card['suit'], card['value'])
				else:
					hands[player] += card_html.format('unclickable', card['suit'], card['value'])
		else:
			# Add unclickable card backs to hand
			hands['top_hand'] = card_back * len(game['hands'][player]['cards'])

	return hands

# Prepare middle cards for display
def prepare_middle(game, client):
	middle = ''

	# If in bidding round
	if game['round'] == -1:
		# If this user is the current bidder
		if client == game['players'][game['active_player']]:
			# If the user is also the dealer
			if client == game['players'][game['dealer']]:
				return match_pass_buttons.format(game['bid'])
			else:
				return bid_buttons

	else:
		# If there are cards in play, show them
		for card in game['middle_cards']['cards']:
			if card['suit'] == game['trump']:
				card_class = 'trump'
			else:
				card_class = ''
			middle += card_html.format(card_class, card['suit'], card['value'])

		return middle
