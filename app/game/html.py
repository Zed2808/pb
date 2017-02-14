# Button for advancing non-player action
adv_button = '<button id="adv_button" type="button">Next</button>'

# Buttons for bidding
bid_buttons = '''
	<button class="bid_button" type="button" value="0">Pass</button>
	<button class="bid_button" type="button" value="2">2</button>
	<button class="bid_button" type="button" value="3">3</button>
	<button class="bid_button" type="button" value="4">4</button>'''
match_pass_buttons = '''
	<button class="bid_button" type="button" value="0">Pass</button><
	<button class="bid_button" type="button" value="{0}">Match ({0})</button>'''

# HTML for displaying a card image
card_clickable_html = '<input type="image" class="card clickable {}" value="{}" src="static/img/cards/{}_{}.png">'
card_html = '<img class="card {}" src="static/img/cards/{}_{}.png">'
card_back = '<img class="card" src="static/img/cards/back.png">'
