from flask import session, render_template, request, jsonify
from app import app
from .game.deck import new_card, new_deck, push_back, pop_back, sort_deck

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

@app.route('/bid')
def bid():
	bid = request.args.get('bid', 0, type=int)
	session['bid'] = bid
	session['min_bid'] = bid + 1
	session['bidder'] = session['active_player']
	return jsonify(player=session['active_player'], bid=bid)
