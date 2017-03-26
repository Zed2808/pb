from flask import Flask, render_template, jsonify, abort
from .game.game import *

app = Flask(__name__)
app.secret_key = 'SuperSecretKey'

games = []

@app.route('/')
@app.route('/index')
def index():
	# Initialize the game state
	game = create_new_game(games)

	return render_template('index.html', game=game)

@app.route('/do_action/<int:game_id>', methods=['GET', 'POST'])
def do_action(game_id):
	# Get game with ID = game_id
	game = [game for game in games if game['id'] == game_id]

	# If game with game_id does not exist, return 404
	if len(game) == 0:
		abort(404)

	game = game[0]

	# Strings to return to display are reset to empty
	reset_returns(game)

	# Make sure players don't have cards yet
	if not game['hands_dealt']:
		# Full hands are randomly dealt to each player
		deal_hands(game)

	# Bidding round
	elif game['round'] == -1:
		# Active player places their bid
		bidding_round(game)

	# Regular rounds
	else:
		# Active player plays a card
		play_card(game)

		# Round is over: collect the tricks and prepare a new round
		if game['round_over']:
			end_round(game)

		# Prepare for next turn
		game['turn'] += 1

		# Last turn completed
		if game['turn'] >= game['num_players']:
			end_turn(game)

		print('>>> END OF TURN')

	prepare_hands(game)

	prepare_middle(game)

	prepare_names(game)

	return jsonify(top_name=game['top_name'],
		           top_hand=game['top_hand'],
		           middle=game['middle'],
		           bottom_hand=game['bottom_hand'],
		           bottom_name=game['bottom_name'],
		           bottom=game['bottom'],
		           log=game['log'])
