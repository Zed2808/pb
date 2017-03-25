from flask import request
from collections import defaultdict
from .deck import *
from .html import *
from .pb import *

# Initialize the gamestate session variables
def init_gamestate(session):
	session['num_players'] = 2
	session['hand_size'] = 6
	session['dealer'] = 0
	session['active_player'] = 1
	session['min_bid'] = 2
	session['bid'] = 0
	session['bidder'] = -1
	session['round'] = -1
	session['round_over'] = False
	session['turn'] = -1
	session['taker'] = -1
	session['played_card'] = new_card()
	session['top_card'] = new_card()
	session['trump'] = 0
	session['trump_set'] = False
	session['lead_suit'] = 0
	session['deck'] = new_deck(filled=True, shuffled=True)
	session['middle_cards'] = new_deck()
	session['hands'] = []
	session['hands_dealt'] = False
	session['tricks'] = []
	session['scores'] = []
	session['score_limit'] = 11

	reset_returns(session)

	# create hand, trick pile, and score for each player
	for player in range(session['num_players']):
		session['hands'].append(new_deck())
		session['tricks'].append(new_deck())
		session['scores'].append(0)

# Advance active_player, looping if necessary
def next_player(session):
	session['active_player'] += 1
	if session['active_player'] >= session['num_players']:
		session['active_player'] = 0

# Advance to next dealer, looping if necessary
def next_dealer(session):
	session['dealer'] += 1
	if session['dealer'] >= session['num_players']:
		session['dealer'] = 0

# Reset HTML return strings
def reset_returns(session):
	session['top_name'] = ''
	session['top_hand'] = ''
	session['middle'] = ''
	session['bottom_hand'] = ''
	session['bottom_name'] = ''
	session['bottom'] = ''
	session['log'] = ''

# Deal hands to players
def deal_hands(session):
	# Re-make the deck before dealing new hands
	session['deck'] = new_deck(filled=True, shuffled=True)

	# Deal hand to each player
	print('>>> Dealing hands')
	for player in range(session['num_players']):
		# Deal cards up to hand_size
		for n in range(session['hand_size']):
			# Get card from the deck
			card = pop_back(session['deck'])

			# Add card to player's hand
			push_back(session['hands'][player], card)

	# If human is bidding first, show bid buttons
	if session['active_player'] == 0:
		session['middle'] = bid_buttons
	else:
		session['bottom'] = adv_button

	session['log'] += '<p><b>Player {}</b> bids first.</p>'.format(session['active_player']+1)
	session['hands_dealt'] = True

# Perform a turn of the bidding round
def bidding_round(session):
	# As long as we haven't reached the dealer yet
	if session['active_player'] != session['dealer']:
		print('>>> dealer not bidding')
		# Player's bid
		if session['active_player'] == 0:
			bid = request.args.get('bid', 0, type=int)
			session['bottom'] = adv_button
		# Bot's bid
		else:
			bid = PB.action(session)
			# If bot doesn't pass
			if bid != 0:
				# Bid is valid
				if bid in range(2, 5):
					session['middle'] = match_pass_buttons.format(bid)
				# Default an invalid bid to 0
				else:
					bid = 0

		# Not pass
		if bid != 0:
			# Set bid, bidder, new min_bid
			session['bid'] = bid
			session['min_bid'] = bid + 1
			session['bidder'] = session['active_player']
			print('>>> player {} bid {}'.format(session['active_player'], bid))
			session['log'] = '<p><b>Player {}</b> bid {}.</p>'.format(session['bidder']+1, bid)
		# Pass
		else:
			print('>>> player {} passes'.format(session['active_player']))
			session['log'] = '<p><b>Player {}</b> passes.</p>'.format(session['active_player']+1)

		# Prepare for next player
		next_player(session)

		# Check if dealer's hand is forced
		if session['active_player'] == session['dealer'] and session['bid'] < 2:
			session['bid'] = session['min_bid']
			session['bidder'] = session['active_player']

			print('>>> player {} is forced to bid {}'.format(session['active_player'], session['bid']))

			session['log'] += '<p><b>Player {}</b> is forced to bid {}.</p>'.format(session['bidder']+1, session['bid'])
			session['middle'] = ''
			session['bottom'] = adv_button

			#Prepare for first round
			session['round'] = 0

	# If others have bid, dealer can still match or pass
	else:
		# Human
		if session['active_player'] == 0:
			bid = request.args.get('bid', 0, type=int)
		# Bot
		else:
			bid = PB.action(session)
			if bid not in range(2, 5) and bid != 0:
				bid = 0

		# Dealer passes
		if bid == 0:
			session['bottom'] = adv_button
			session['log'] = '<p><b>Player {}</b> passes.</p>'.format(session['active_player']+1)
		# Dealer matches
		else:
			session['log'] = '<p><b>Player {}</b> matches <b>Player {}</b>\'s bid of {}.</p>'.format(session['active_player']+1,
				                                                                   session['bidder']+1,
				                                                                   session['bid'])
			session['bidder'] = session['active_player']
			session['bottom'] = adv_button

		#Prepare for first round
		session['round'] = 0
		session['turn'] = -1

# Play a card
def play_card(session):
	print('>>> HAND IN PROGRESS')
	print('>>> ROUND {} IN PROGRESS'.format(session['round']))
	print('>>> START OF TURN {}'.format(session['turn']))
	print('>>> active_player: {}'.format(session['active_player']))

	# If start of the hand
	if session['round'] == 0 and session['turn'] == -1:
		# Log who is leading out
		session['log'] = '<p><b>Player {}</b> won the bid and is leading out.</p>'.format(session['bidder']+1)
		session['active_player'] = session['bidder']

		# Show adv_button if bot is leading
		if session['active_player'] != 0:
			session['bottom'] = adv_button

	# Actual game turns
	elif session['turn'] > -1 and session['turn'] < session['num_players']:
		# Playing a card
		# Human's turn
		if session['active_player'] == 0:
			choice = request.args.get('card', 0, type=int)

			# Enable adv_button
			session['bottom'] = adv_button
		# Bot's turn
		else:
			choice = PB.action(session)
			if choice not in range(playable_cards(session['hands'][1], session)):
				choice = 0

		# Set played card from player's choice
		session['played_card'] = remove_card(session['hands'][session['active_player']], choice)
		print('>>> Player {} played the {}.'.format(session['active_player'], card_to_string(session['played_card'])))

		session['log'] += '<p><b>Player {}</b> played the {}.</p>'.format(session['active_player']+1, card_to_string(session['played_card']))

		# If leading the round
		if session['turn'] == 0:
			print('>>> Player {} leads the hand'.format(session['active_player']))

			# Set lead suit, initial taker, top card, round_over
			session['lead_suit'] = session['played_card']['suit']
			session['taker'] = session['active_player']
			session['top_card'] = session['played_card']

			# Set trump if first round
			if session['round'] == 0:
				print('>>> Player {} sets trump as {}'.format(session['active_player'], suit_to_string(session['played_card']['suit'])))
				session['trump'] = session['played_card']['suit']
				session['trump_set'] = True
				session['log'] += '<p>Trump is now <b>{}</b>.</p>'.format(suit_to_string(session['played_card']['suit']))
		# Otherwise, check if card beats top
		else:
			check_if_new_top(session)

		# Move played card to middle, prepare to display
		push_back(session['middle_cards'], session['played_card'])

		# Prepare for next player
		next_player(session)

# Check if the played card is the new top card and set variables accordingly
def check_if_new_top(session):
	# Current top is trump
	if session['top_card']['suit'] == session['trump']:
		# Played card is also trump
		if session['played_card']['suit'] == session['trump']:
			# Played value beats top value
			if session['played_card']['value'] > session['top_card']['value']:
				print('>>> Player {} sets new top card'.format(session['active_player']))
				# Set new top & taker
				session['top_card'] = session['played_card']
				session['taker'] = session['active_player']
	# Current top is not trump (must be lead)
	else:
		# Played card is trump
		if session['played_card']['suit'] == session['trump']:
			print('>>> Player {} sets new top card'.format(session['active_player']))
			# Set new top & taker
			session['top_card'] = session['played_card']
			session['taker'] = session['active_player']
		# Played card is lead suit
		elif session['played_card']['suit'] == session['lead_suit']:
			# Played card value beats top value
			if session['played_card']['value'] > session['top_card']['value']:
				print('>>> Player {} sets new top card'.format(session['active_player']))
				# Set new top & taker
				session['top_card'] = session['played_card']
				session['taker'] = session['active_player']

# End the turn
def end_turn(session):
	print('>>> all turns completed')

	# Taker takes trick
	print('>>> Player {} takes the trick'.format(session['taker']))
	session['log'] += '<p><b>Player {}</b> takes the trick.</p>'.format(session['taker']+1)

	session['round_over'] = True
	session['bottom'] = adv_button

# End the round, score hands and prepare for new hand if necessary
def end_round(session):
	print('>>> ROUND {} OVER: COLLECTING TRICK'.format(session['round']))

	# Collect trick for taker
	for card in range(session['num_players']):
		push_back(session['tricks'][session['taker']], pop_back(session['middle_cards']))

	session['round_over'] = False
	session['round'] += 1
	print('>>> advancing to round {}'.format(session['round']))
	session['turn'] = -1
	session['active_player'] = session['taker']

	# If bot will lead next round, show adv_button
	if session['active_player'] != 0:
		session['bottom'] = adv_button

	# Last round of the hand
	if session['round'] >= session['hand_size']:
		# Score hands
		print('>>> SCORING HANDS')
		session['log'] += score_hands(session)

		# Prepare for a new hand
		session['bottom'] = adv_button
		session['hands_dealt'] = False
		session['trump_set'] = False
		session['round'] = -1
		next_dealer(session)
		session['active_player'] = session['dealer']
		next_player(session)
		session['min_bid'] = 2
		session['bid'] = 0
		session['bidder'] = -1

# Score hands and modify game state
def score_hands(session):
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
	for player in range(session['num_players']):
		# Append a 0 to hand_scores and pips for each player
		hand_scores.append(0)
		pips.append(0)

		# For each card in the trick stack
		for card in session['tricks'][player]['cards']:
			# If card is trump
			if card['suit'] == session['trump']:
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
	for player in range(session['num_players']):
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

	for player in range(session['num_players']):
		# If player was the bidder
		if player == session['bidder']:
			# If bidder does not make their bid
			if hand_scores[player] < session['bid']:
				# Set hand score to -bid
				hand_scores[session['bidder']] = -(session['bid'])
				msg += '<p><b>Player {0}</b> did not make their bid of {1} and loses {1} points.</p>'.format(player+1, session['bid'])
			# Bidder did make their bid
			else:
				msg += '<p><b>Player {}</b> made their bid of {} and gets {} points.</p>'.format(player+1, session['bid'], hand_scores[player])
		# Player was not the bidder
		elif hand_scores[player] > 0:
			msg += '<p><b>Player {}</b> gets {} points.</p>'.format(player+1, hand_scores[player])

	# Add hand scores to game scores
	for player in range(session['num_players']):
		session['scores'][player] += hand_scores[player]

	return msg

# Prepare hands for display
def prepare_hands(session):
	# Prepare hands for display
	for player in range(session['num_players']):
		# Sort hands
		sort_deck(session['hands'][player], session)

		# Get number of playable cards in hand
		playable = playable_cards(session['hands'][player], session)

		# Add card html to display
		for n in range(len(session['hands'][player]['cards'])):
			card = session['hands'][player]['cards'][n]

			# If human's hand
			if player == 0:
				# If human about to go, card is playable, round is not over, and round is not bidding round, make cards clickable
				if session['active_player'] == 0 and n in range(playable) and session['round_over'] == False and session['round'] > -1:
					# If card is trump and there is a trump
					if card['suit'] == session['trump'] and session['trump_set']:
						card_class = 'trump'
					else:
						card_class = ''
					session['bottom_hand'] += card_clickable_html.format(card_class, n, card['suit'], card['value'])
				else:
					session['bottom_hand'] += card_html.format('unclickable', card['suit'], card['value'])
			# Bot's hand
			else:
				# Add card back to be displayed
				session['top_hand'] += card_back
				# session['top_hand'] += card_html.format('unclickable', card['suit'], card['value'])

# Prepare middle cards for display
def prepare_middle(session):
	for card in session['middle_cards']['cards']:
		if card['suit'] == session['trump']:
			card_class = 'trump'
		else:
			card_class = ''
		session['middle'] += card_html.format(card_class, card['suit'], card['value'])

# Set the name fields to return to display
def prepare_names(session):
	# Human is the dealer
	if session['dealer'] == 0:
		session['top_name'] = '<p><b>Player 2</b>: {} points</p>'.format(session['scores'][1])
		session['bottom_name'] = '<p><b>Player 1</b> (dealer): {} points</p>'.format(session['scores'][0])
	# Bot is the dealer
	else:
		session['top_name'] = '<p><b>Player 2</b> (dealer): {} points</p>'.format(session['scores'][1])
		session['bottom_name'] = '<p><b>Player 1</b>: {} points</p>'.format(session['scores'][0])
