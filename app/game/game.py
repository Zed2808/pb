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
