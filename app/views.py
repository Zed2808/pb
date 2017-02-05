from flask import session, render_template, request, jsonify
from app import app
from .game.deck import new_card, new_deck, push_back, pop_back, sort_deck
from .game.pb import PB
from .game.game import next_player, next_dealer

@app.route('/')
@app.route('/index')
def index():
	# Initialize the game state
	session['num_players'] = 2
	session['hand_size'] = 6
	session['dealer'] = 0
	session['active_player'] = 1
	session['min_bid'] = 2
	session['bid'] = 0
	session['bidder'] = -1
	session['round'] = -1
	session['turn'] = 0
	session['taker'] = -1
	session['top_card'] = new_card()
	session['trump'] = 0
	session['lead_suit'] = 0
	session['deck'] = new_deck(filled=True, shuffled=True)
	session['middle'] = new_deck()
	session['hands'] = []
	session['tricks'] = []
	session['scores'] = []
	session['score_limit'] = 11

	# create hand, trick pile, and score for each player
	for player in range(session['num_players']):
		session['hands'].append(new_deck())
		session['tricks'].append(new_deck())
		session['scores'].append(0)

	# PLACEHOLDER - Deal some cards to the players
	# for player in range(session['num_players']):
	# 	for card in range(session['hand_size']):
	# 		push_back(session['hands'][player], pop_back(session['deck']))
	# 	# Sort hands
	# 	sort_deck(session['hands'][player], session['trump'], session['lead_suit'])

	return render_template('index.html')

@app.route('/do_action')
def do_action():
	# Bidding round
	if session['round'] == -1:
		# As long as we haven't reached the dealer yet
		if session['active_player'] != session['dealer']:
			# Player's bid
			if session['active_player'] == 0:
				bid = request.args.get('bid', 0, type=int)
			# Bot's bid
			else:
				bid = PB.action(session)

			# Not pass
			if bid != 0:
				# Set bid, bidder, new min_bid
				session['bid'] = bid
				session['min_bid'] = bid + 1
				session['bidder'] = session['active_player']
				msg = '<b>Player {}</b> bid {}.'.format(session['bidder']+1, bid)
			# Pass
			else:
				msg = '<b>Player {}</b> passes the bid.'.format(session['active_player']+1)

			# Prepare for next player
			next_player(session)

			# Check if dealer's hand is forced
			if session['active_player'] == session['dealer'] and session['bid'] < 2:
				session['bid'] = session['min_bid']
				session['bidder'] = session['active_player']

				msg += '<br><b>Player {}</b> is forced to bid {}.'.format(session['bidder']+1, session['bid'])

				# Prepare for next round
				session['round'] = 0

			return jsonify(msg=msg, middle='')

			# If player is next
			if session['active_player'] == 0:
				buttons = '''
					<table>
						<tr>
							<td><button class="bid_button" type="button" value="0">Pass</button></td>
							<td><button class="bid_button" type="button" value="2">Bid 2</button></td>
							<td><button class="bid_button" type="button" value="3">Bid 3</button></td>
							<td><button class="bid_button" type="button" value="4">Bid 4</button></td>
						</tr>
					</table>'''
			return jsonify(msg=msg, middle=buttons)
		# If others have bid, dealer can still match or pass
		else:
			# Human
			if session['active_player'] == 0:
				bid = request.args.get('bid', 0, type=int)
			# Bot
			else:
				bid = PB.bid(session)

			# Dealer passes
			if bid == 0:
				# Prepare for first round
				session['round'] = 0
				return jsonify(msg='<b>Player {}</b> passes.'.format(session['active_player']+1), middle='')
			# Dealer matches
			else:
				msg = '<b>Player {}</b> matches <b>Player {}</b>\'s bid of {}.'.format(session['active_player']+1,
					                                                                   session['bidder']+1,
					                                                                   session['bid'])
				session['bidder'] = session['active_player']
				#Prepare for first round
				session['round'] = 0
				return jsonify(msg=msg, middle='')
	# Regular rounds
	# else:
		# First round
		# if session['round'] == 0:
			# Deal hands
