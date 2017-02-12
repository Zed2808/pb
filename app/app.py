from flask import Flask, session, render_template, jsonify
from .game.game import *

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
	# Strings to return to display are reset to empty
	reset_returns(session)

	# Make sure players don't have cards yet
	if not session['hands_dealt']:
		# Full hands are randomly dealt to each player
		deal_hands(session)

	# Bidding round
	if session['round'] == -1:
		# Active player places their bid
		bidding_round(session)

	# Regular rounds
	else:
		# Active player plays a card
		play_card(session)

		# Round is over: collect the tricks and prepare a new round
		if session['round_over']:
			end_round(session)

		# Prepare for next turn
		session['turn'] += 1

		# Last turn completed
		if session['turn'] >= session['num_players']:
			end_turn(session)

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
