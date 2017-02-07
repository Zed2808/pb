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

	# If bidder does not make their bid
	if hand_scores[session['bidder']] < session['bid']:
		# Lose points equal to bid, set hand score to 0
		session['scores'][session['bidder']] -= session['bid']
		hand_scores[session['bidder']] = 0

	# Add hand scores to game scores
	for player in range(session['num_players']):
		session['scores'][player] += hand_scores[player]

	# Return log message
	msg = '<b>Player {}</b> took high.'.format(high_taker + 1)
	msg += '<br><b>Player {}</b> took low.'.format(low_taker + 1)
	if jack_taker > -1:
		msg += '<br><b>Player {}</b> took jack.'.format(jack_taker + 1)
	if game_taker > -1:
		msg += '<br><b>Player {}</b> took game.'.format(game_taker + 1)
	else:
		msg += '<br>Players tied for game.'

	return msg
