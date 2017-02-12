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

	# Make sure players don't have cards yet
	if not session['hands_dealt']:
		deal_hands(session)

	# Bidding round
	if session['round'] == -1:
		bidding_round(session)

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

	prepare_hands(session)

	prepare_middle(session)

	prepare_names(session)

	return jsonify(top_name=session['top_name'],
		           top_hand=session['top_hand'],
		           middle=session['middle'],
		           bottom_hand=session['bottom_hand'],
		           bottom_name=session['bottom_name'],
		           bottom=session['bottom'],
		           log=session['log'])
