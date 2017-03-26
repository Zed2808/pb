$(document).ready(function() {
	$('#middle').on('click', '.bid_button', function() {
		$.getJSON('/do_action/0', {
			bid: $(this).attr('value')
		}, function(data) {
			$('#top_name').html(data.top_name);
			$('#top_hand').html(data.top_hand);
			$('#middle').html(data.middle);
			$('#bottom_hand').html(data.bottom_hand);
			$('#bottom_name').html(data.bottom_name);
			$('#bottom').html(data.bottom);
			$('#log').html(data.log);
		});
	});

	$('#bottom').on('click', '#adv_button', function() {
		$.getJSON('/do_action/0', {},
			function(data) {
				$('#top_name').html(data.top_name);
				$('#top_hand').html(data.top_hand);
				$('#middle').html(data.middle);
				$('#bottom_hand').html(data.bottom_hand);
				$('#bottom_name').html(data.bottom_name);
				$('#bottom').html(data.bottom);
				$('#log').html(data.log);
			}
		);
	});

	$('#bottom_hand').on('click', '.clickable', function() {
		$.getJSON('/do_action/0', {
			card: $(this).val()
		}, function(data) {
			$('#top_name').html(data.top_name);
			$('#top_hand').html(data.top_hand);
			$('#middle').html(data.middle);
			$('#bottom_hand').html(data.bottom_hand);
			$('#bottom_name').html(data.bottom_name);
			$('#bottom').html(data.bottom);
			$('#log').html(data.log);
		});
	});
});
