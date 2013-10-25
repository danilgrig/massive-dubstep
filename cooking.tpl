<!DOCTYPE html>
<html>

	<head>
		<title>Cooking in hostel </title>
	</head>
	
	<body>
	[% FOREACH err = errors %]
		<li>  [% err %] </>
	[% END %]
		<table border="1">
			<tr>
				<td>Name </td>
				<td>Edok </td>
				<td>Cooker </td>
				<td>Score </td>
				<td>Feeding </td>
			</tr>
			[% FOREACH p = people.keys %]
				<tr>
					<td>[% p %] </td>
					<td><input type="checkbox" class="checkbox" value="[% p %]"/> [% people.$p.eaten %] </td>
					<td><input type="radio" class="radio" name = "radio" value="[% p %]" /> [% people.$p.cooked %] </td>
					<td>[% people.$p.ratio %] </td>
					<td>[% people.$p.fed %] </td>
				</tr>
			[% END %]
		</table>
		<button type="button" onclick="send()">submit </>
		<button type="button" onclick="home()">home </>
	</body>

<script type=text/javascript>
function send() {
	var s = document.URL;
	s += "?event=cooked&";
	
	s += "cook=";
	var radios = document.getElementsByClassName("radio");
	var j = 0;
	for (var i = 0; i < radios.length; i++) {
		if (radios[i].checked) {
			if (j != 0) {
				s += ",";
			}
			s += radios[i].value;
			j++;
		}
	}
	
	s += "&"
	
	s += "mouths=";
	var checks = document.getElementsByClassName("checkbox");
	j = 0;
	for (var i = 0; i < checks.length; i++) {
		if (checks[i].checked) {
			if (j != 0) {
				s += ",";
			}
			s += checks[i].value;
			j++;
		}
	}
	window.location = s;
	return false;
}

function home() {
	var s = document.URL;
	s = s.slice(0, 4+s.indexOf(".cgi"));
	window.location = s;
	return false;
}

</script>
	
</html>