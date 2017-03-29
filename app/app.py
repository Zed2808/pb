from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit, join_room
from game.game import *

app = Flask(__name__)
app.secret_key = 'SuperSecretKey'
socketio = SocketIO(app)

games = []

@app.route('/')
def index():
	return render_template('index.html')

# On client connection, generate a game ID for them and send it back
@socketio.on('connect')
def connect():
	print(f'>>> Player ({request.sid}) connected')

@socketio.on('disconnect')
def disconnect():
	print(f'>>> Player ({request.sid}) disconnected')

# When player joins a room, create a new game if it doesn't already exist
@socketio.on('join')
def join(msg={'game_id': ''}):
	# Generate new game id if not given one
	if msg['game_id'] == '':
		game_id = new_game_id()
	else:
		game_id = msg['game_id']

	join_room(game_id)
	print(f'>>> Player ({request.sid}) joined game {game_id}')

	# Get game if it exists already
	game = get_game(games, game_id)

	# If game does not yet exist, create it
	if game is None:
		game = create_new_game(games, game_id)

	emit('new_game', {'game_id': game['id']})

@socketio.on('deal')
def deal(msg):
	game = get_game(games, msg['game_id'])

	# Only deal hands if hands have not been dealt yet this round
	if not game['hands_dealt']:
		deal_hands(game)

	emit('update',
		{'hands': prepare_hands(game, 0),
		 'middle': game['middle'],
		 'bottom': game['bottom'],
		 'log': game['log']},
		room=game['id'])

@socketio.on('bid')
def bid(msg):
	game = get_game(games, msg['game_id'])

@socketio.on('action')
def do_action(msg):
	# Bidding round
	if game['round'] == -1:
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

	emit('update', jsonify(top_name=game['top_name'],
				           top_hand=game['top_hand'],
				           middle=game['middle'],
				           bottom_hand=game['bottom_hand'],
				           bottom_name=game['bottom_name'],
				           bottom=game['bottom'],
				           log=game['log']))

if __name__ == '__main__':
	socketio.run(app, debug=True)
