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
		'hands': [],
		'hands_dealt': False,
		'tricks': [],
		'scores': [],
		'score_limit': 11
	}

	# Create hand, trick pile, and score for each player
	for player in range(game['num_players']):
		game['hands'].append(new_deck())
		game['tricks'].append(new_deck())
		game['scores'].append(0)

	# Set empty returns
	reset_returns(game)

	# Append newly created game to list of games
	games.append(game)

	return game

# Generate new 4 letter game ID
def new_game_id():
	game_id = ''
	for x in range(4):
		game_id += random.choice(string.ascii_uppercase)

	return game_id

# Return game given its game ID
def get_game(games, game_id):
	game = [game for game in games if game['id'] == game_id]
	if len(game) == 0:
		return None
	return game[0]

# Advance active_player, looping if necessary
def next_player(game):
	game['active_player'] += 1
	if game['active_player'] >= game['num_players']:
		game['active_player'] = 0

# Advance to next dealer, looping if necessary
def next_dealer(game):
	game['dealer'] += 1
	if game['dealer'] >= game['num_players']:
		game['dealer'] = 0

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
	print('>>> Dealing hands')
	for player in range(game['num_players']):
		# Deal cards up to hand_size
		for n in range(game['hand_size']):
			# Get card from the deck
			card = pop_back(game['deck'])

			# Add card to player's hand
			push_back(game['hands'][player], card)

	game['log'] += '<p><b>Player {}</b> bids first.</p>'.format(game['active_player']+1)
	game['hands_dealt'] = True

# Perform a turn of the bidding round
def bidding_round(game):
	# As long as we haven't reached the dealer yet
	if game['active_player'] != game['dealer']:
		print('>>> dealer not bidding')
		# Player's bid
		if game['active_player'] == 0:
			bid = request.args.get('bid', 0, type=int)
			game['bottom'] = adv_button
		# Bot's bid
		else:
			bid = PB.action(game)
			# If bot doesn't pass
			if bid != 0:
				# Bid is valid
				if bid in range(2, 5):
					game['middle'] = match_pass_buttons.format(bid)
				# Default an invalid bid to 0
				else:
					bid = 0

		# Not pass
		if bid != 0:
			# Set bid, bidder, new min_bid
			game['bid'] = bid
			game['min_bid'] = bid + 1
			game['bidder'] = game['active_player']
			print('>>> player {} bid {}'.format(game['active_player'], bid))
			game['log'] = '<p><b>Player {}</b> bid {}.</p>'.format(game['bidder']+1, bid)
		# Pass
		else:
			print('>>> player {} passes'.format(game['active_player']))
			game['log'] = '<p><b>Player {}</b> passes.</p>'.format(game['active_player']+1)

		# Prepare for next player
		next_player(game)

		# Check if dealer's hand is forced
		if game['active_player'] == game['dealer'] and game['bid'] < 2:
			game['bid'] = game['min_bid']
			game['bidder'] = game['active_player']

			print('>>> player {} is forced to bid {}'.format(game['active_player'], game['bid']))

			game['log'] += '<p><b>Player {}</b> is forced to bid {}.</p>'.format(game['bidder']+1, game['bid'])
			game['middle'] = ''
			game['bottom'] = adv_button

			#Prepare for first round
			game['round'] = 0

	# If others have bid, dealer can still match or pass
	else:
		# Human
		if game['active_player'] == 0:
			bid = request.args.get('bid', 0, type=int)
		# Bot
		else:
			bid = PB.action(game)
			if bid not in range(2, 5) and bid != 0:
				bid = 0

		# Dealer passes
		if bid == 0:
			game['bottom'] = adv_button
			game['log'] = '<p><b>Player {}</b> passes.</p>'.format(game['active_player']+1)
		# Dealer matches
		else:
			game['log'] = '<p><b>Player {}</b> matches <b>Player {}</b>\'s bid of {}.</p>'.format(game['active_player']+1,
				                                                                   game['bidder']+1,
				                                                                   game['bid'])
			game['bidder'] = game['active_player']
			game['bottom'] = adv_button

		#Prepare for first round
		game['round'] = 0
		game['turn'] = -1

# Play a card
def play_card(game):
	print('>>> HAND IN PROGRESS')
	print('>>> ROUND {} IN PROGRESS'.format(game['round']))
	print('>>> START OF TURN {}'.format(game['turn']))
	print('>>> active_player: {}'.format(game['active_player']))

	# If start of the hand
	if game['round'] == 0 and game['turn'] == -1:
		# Log who is leading out
		game['log'] = '<p><b>Player {}</b> won the bid and is leading out.</p>'.format(game['bidder']+1)
		game['active_player'] = game['bidder']

		# Show adv_button if bot is leading
		if game['active_player'] != 0:
			game['bottom'] = adv_button

	# Actual game turns
	elif game['turn'] > -1 and game['turn'] < game['num_players']:
		# Playing a card
		# Human's turn
		if game['active_player'] == 0:
			choice = request.args.get('card', 0, type=int)

			# Enable adv_button
			game['bottom'] = adv_button
		# Bot's turn
		else:
			choice = PB.action(game)
			if choice not in range(playable_cards(game['hands'][1], game)):
				choice = 0

		# Set played card from player's choice
		game['played_card'] = remove_card(game['hands'][game['active_player']], choice)
		print('>>> Player {} played the {}.'.format(game['active_player'], card_to_string(game['played_card'])))

		game['log'] += '<p><b>Player {}</b> played the {}.</p>'.format(game['active_player']+1, card_to_string(game['played_card']))

		# If leading the round
		if game['turn'] == 0:
			print('>>> Player {} leads the hand'.format(game['active_player']))

			# Set lead suit, initial taker, top card, round_over
			game['lead_suit'] = game['played_card']['suit']
			game['taker'] = game['active_player']
			game['top_card'] = game['played_card']

			# Set trump if first round
			if game['round'] == 0:
				print('>>> Player {} sets trump as {}'.format(game['active_player'], suit_to_string(game['played_card']['suit'])))
				game['trump'] = game['played_card']['suit']
				game['trump_set'] = True
				game['log'] += '<p>Trump is now <b>{}</b>.</p>'.format(suit_to_string(game['played_card']['suit']))
		# Otherwise, check if card beats top
		else:
			check_if_new_top(game)

		# Move played card to middle, prepare to display
		push_back(game['middle_cards'], game['played_card'])

		# Prepare for next player
		next_player(game)

# Check if the played card is the new top card and set variables accordingly
def check_if_new_top(game):
	# Current top is trump
	if game['top_card']['suit'] == game['trump']:
		# Played card is also trump
		if game['played_card']['suit'] == game['trump']:
			# Played value beats top value
			if game['played_card']['value'] > game['top_card']['value']:
				print('>>> Player {} sets new top card'.format(game['active_player']))
				# Set new top & taker
				game['top_card'] = game['played_card']
				game['taker'] = game['active_player']
	# Current top is not trump (must be lead)
	else:
		# Played card is trump
		if game['played_card']['suit'] == game['trump']:
			print('>>> Player {} sets new top card'.format(game['active_player']))
			# Set new top & taker
			game['top_card'] = game['played_card']
			game['taker'] = game['active_player']
		# Played card is lead suit
		elif game['played_card']['suit'] == game['lead_suit']:
			# Played card value beats top value
			if game['played_card']['value'] > game['top_card']['value']:
				print('>>> Player {} sets new top card'.format(game['active_player']))
				# Set new top & taker
				game['top_card'] = game['played_card']
				game['taker'] = game['active_player']

# End the turn
def end_turn(game):
	print('>>> all turns completed')

	# Taker takes trick
	print('>>> Player {} takes the trick'.format(game['taker']))
	game['log'] += '<p><b>Player {}</b> takes the trick.</p>'.format(game['taker']+1)

	game['round_over'] = True
	game['bottom'] = adv_button

# End the round, score hands and prepare for new hand if necessary
def end_round(game):
	print('>>> ROUND {} OVER: COLLECTING TRICK'.format(game['round']))

	# Collect trick for taker
	for card in range(game['num_players']):
		push_back(game['tricks'][game['taker']], pop_back(game['middle_cards']))

	game['round_over'] = False
	game['round'] += 1
	print('>>> advancing to round {}'.format(game['round']))
	game['turn'] = -1
	game['active_player'] = game['taker']

	# If bot will lead next round, show adv_button
	if game['active_player'] != 0:
		game['bottom'] = adv_button

	# Last round of the hand
	if game['round'] >= game['hand_size']:
		# Score hands
		print('>>> SCORING HANDS')
		game['log'] += score_hands(game)

		# Prepare for a new hand
		game['bottom'] = adv_button
		game['hands_dealt'] = False
		game['trump_set'] = False
		game['round'] = -1
		next_dealer(game)
		game['active_player'] = game['dealer']
		next_player(game)
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

	# Prepare hands for display
	for player in range(game['num_players']):
		# Create empty placeholder for player's hand
		hands[player] = ''

		# Sort hands
		sort_deck(game['hands'][player], game)

		# Get number of playable cards in hand
		playable = playable_cards(game['hands'][player], game)

		# Add card html to display
		for n in range(len(game['hands'][player]['cards'])):
			card = game['hands'][player]['cards'][n]

			# If client's hand
			if player == client:
				# If client about to go, card is playable, round is not over, and round is not bidding round, make cards clickable
				if game['active_player'] == client and n in range(playable) and game['round_over'] == False and game['round'] > -1:
					# If card is trump and there is a trump
					if card['suit'] == game['trump'] and game['trump_set']:
						card_class = 'trump'
					else:
						card_class = ''
					hands[player] += card_clickable_html.format(card_class, n, card['suit'], card['value'])
				else:
					hands[player] += card_html.format('unclickable', card['suit'], card['value'])
			# Bot's hand
			else:
				# Add card back to be displayed
				hands[player] += card_back
				# hands[player] += card_html.format('unclickable', card['suit'], card['value'])

	return hands

# Prepare middle cards for display
def prepare_middle(game):
	for card in game['middle_cards']['cards']:
		if card['suit'] == game['trump']:
			card_class = 'trump'
		else:
			card_class = ''
		game['middle'] += card_html.format(card_class, card['suit'], card['value'])

# Set the name fields to return to display
def prepare_names(game):
	# Human is the dealer
	if game['dealer'] == 0:
		game['top_name'] = '<p><b>Player 2</b>: {} points</p>'.format(game['scores'][1])
		game['bottom_name'] = '<p><b>Player 1</b> (dealer): {} points</p>'.format(game['scores'][0])
	# Bot is the dealer
	else:
		game['top_name'] = '<p><b>Player 2</b> (dealer): {} points</p>'.format(game['scores'][1])
		game['bottom_name'] = '<p><b>Player 1</b>: {} points</p>'.format(game['scores'][0])
