from collections import defaultdict

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

# Score hands and modify game state
def score_hands(session):
	high_trump = 0
	low_trump = 14
	jack_taker = -1
	game_taker = -1
	round_scores = []
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
		# Append a 0 to round_scores and pips for each player
		round_scores.append(0)
		pips.append(0)

		# For each card in the trick stack
		for card in range(session['tricks'][player]['cards']):
			print('carderoo')
