from flask import Flask, session, render_template, request, jsonify
from .game.deck import *
from .game.game import *
from .game.pb import *
from .game.html import *

app = Flask(__name__)
app.secret_key = 'SuperSecretKey'

@app.route('/')
@app.route('/index')
def index():
	# Initialize the game state
	init_gamestate(session)

	return render_template('index.html')

@app.route('/do_action')
def do_action():
	reset_returns(session)

	# Make sure players have cards
	if not session['hands_dealt']:
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

		session['log'] += '<b>Player {}</b> bids first.'.format(session['active_player']+1)
		session['hands_dealt'] = True

	# Bidding round
	elif session['round'] == -1:
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
				session['log'] = '<b>Player {}</b> bid {}.'.format(session['bidder']+1, bid)
			# Pass
			else:
				print('>>> player {} passes'.format(session['active_player']))
				session['log'] = '<b>Player {}</b> passes.'.format(session['active_player']+1)

			# Prepare for next player
			next_player(session)

			# Check if dealer's hand is forced
			if session['active_player'] == session['dealer'] and session['bid'] < 2:
				session['bid'] = session['min_bid']
				session['bidder'] = session['active_player']

				print('>>> player {} is forced to bid {}'.format(session['active_player'], session['bid']))

				session['log'] += '<br><b>Player {}</b> is forced to bid {}.'.format(session['bidder']+1, session['bid'])
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
				session['log'] = '<b>Player {}</b> passes.'.format(session['active_player']+1)
			# Dealer matches
			else:
				session['log'] = '<b>Player {}</b> matches <b>Player {}</b>\'s bid of {}.'.format(session['active_player']+1,
					                                                                   session['bidder']+1,
					                                                                   session['bid'])
				session['bidder'] = session['active_player']
				session['bottom'] = adv_button

			#Prepare for first round
			session['round'] = 0
			session['turn'] = -1

	# Regular rounds
	else:
		# Hand is complete
		if session['hand_over']:
			print('>>> HAND COMPLETE')
		# Hand is in progress
		else:
			print('>>> HAND IN PROGRESS')
			print('>>> ROUND {} IN PROGRESS'.format(session['round']))
			print('>>> START OF TURN {}'.format(session['turn']))
			print('>>> active_player: {}'.format(session['active_player']))

			# If start of the hand
			if session['round'] == 0 and session['turn'] == -1:
				# Log who is leading out
				session['log'] = '<b>Player {}</b> won the bid and is leading out.'.format(session['bidder']+1)
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
				played_card = remove_card(session['hands'][session['active_player']], choice)
				print('>>> Player {} played the {}.'.format(session['active_player'], card_to_string(played_card)))

				session['log'] += '<b>Player {}</b> played the {}.'.format(session['active_player']+1, card_to_string(played_card))

				# If leading the round
				if session['turn'] == 0:
					print('>>> Player {} leads the hand'.format(session['active_player']))

					# Set lead suit, initial taker, top card, round_over
					session['lead_suit'] = played_card['suit']
					session['taker'] = session['active_player']
					session['top_card'] = played_card

					# Set trump if first round
					if session['round'] == 0:
						print('>>> Player {} sets trump as {}'.format(session['active_player'], suit_to_string(played_card['suit'])))
						session['trump'] = played_card['suit']
						session['trump_set'] = True
						session['log'] += ' Trump is now {}.'.format(suit_to_string(played_card['suit']))
				# Otherwise, check if card beats top
				else:
					# Current top is trump
					if session['top_card']['suit'] == session['trump']:
						# Played card is also trump
						if played_card['suit'] == session['trump']:
							# Played value beats top value
							if played_card['value'] > session['top_card']['value']:
								print('>>> Player {} sets new top card'.format(session['active_player']))
								# Set new top & taker
								session['top_card'] = played_card
								session['taker'] = session['active_player']
					# Current top is not trump (must be lead)
					else:
						# Played card is trump
						if played_card['suit'] == session['trump']:
							print('>>> Player {} sets new top card'.format(session['active_player']))
							# Set new top & taker
							session['top_card'] = played_card
							session['taker'] = session['active_player']
						# Played card is lead suit
						elif played_card['suit'] == session['lead_suit']:
							# Played card value beats top value
							if played_card['value'] > session['top_card']['value']:
								print('>>> Player {} sets new top card'.format(session['active_player']))
								# Set new top & taker
								session['top_card'] = played_card
								session['taker'] = session['active_player']

				# Move played card to middle, prepare to display
				push_back(session['middle_cards'], played_card)

				# Prepare for next player
				next_player(session)

			# Round is over: collect the tricks and prepare a new round
			if session['round_over']:
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

			# Prepare for next turn
			session['turn'] += 1

			# Last turn completed
			if session['turn'] >= session['num_players']:
				print('>>> all turns completed')

				# Taker takes trick
				print('>>> Player {} takes the trick'.format(session['taker']))
				session['log'] += '<br><b>Player {}</b> takes the trick.'.format(session['taker']+1)

				session['round_over'] = True
				session['bottom'] = adv_button

			print('>>> END OF TURN')

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
	for card in session['middle_cards']['cards']:
		if card['suit'] == session['trump']:
			card_class = 'trump'
		else:
			card_class = ''
		session['middle'] += card_html.format(card_class, card['suit'], card['value'])

	# Human is the dealer
	if session['dealer'] == 0:
		session['top_name'] = '<b>Player 2</b>: {} points'.format(session['scores'][1])
		session['bottom_name'] = '<b>Player 1</b> (dealer): {} points'.format(session['scores'][0])
	# Bot is the dealer
	else:
		session['top_name'] = '<b>Player 2</b> (dealer): {} points'.format(session['scores'][1])
		session['bottom_name'] = '<b>Player 1</b>: {} points'.format(session['scores'][0])

	return jsonify(top_name=session['top_name'],
		           top_hand=session['top_hand'],
		           middle=session['middle'],
		           bottom_hand=session['bottom_hand'],
		           bottom_name=session['bottom_name'],
		           bottom=session['bottom'],
		           log=session['log'])
