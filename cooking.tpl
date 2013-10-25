<!DOCTYPE html>
<html>

	<head>
		<title>Cooking in hostel </title>
	</head>
	
	<body>
	[% FOREACH err = errors %]
		<li>  [% err %] </>
	[% END %]
		<table border="1"  align="left">
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
		<div>
			<button type="button" onclick="send()">submit </>
			<button type="button" onclick="home()">home </>
		</div>
		
		<table>
			<tr bgcolor="#00FFFF">
				<td>time </td>
				<td>cook </td>
				<td>mouths </td>
			</tr>
			[% FOREACH l = log.keys.sort.reverse %]
			<tr bgcolor="#FFFFFF">
				<td>[% log.$l.time %] </td>
				<td>[% log.$l.cook %] </td>
				<td>[% FOREACH i = log.$l.mouths.keys %][% log.$l.mouths.$i %] [% END %] </td>
				<td><button value="[% l %]" type="button" onclick="window.location=document.URL+'?event=delete&id='+this.value;return false;">delete </button> </td>
			</tr>
			[% END %]
		</table>
	</body>

<script type=text/javascript>

function send() {
	var s = document.URL;
	s += "?event=cooked&";
	
	s += "cook=";
	var radios = document.getElementsByClassName("radio");
	var j1 = 0;
	for (var i = 0; i < radios.length; i++) {
		if (radios[i].checked) {
			if (j1 != 0) {
				s += ",";
			}
			s += radios[i].value;
			j1 = i + 1;
		}
	}
	
	s += "&"
	
	s += "mouths=";
	var checks = document.getElementsByClassName("checkbox");
	var j2 = 0;
	for (var i = 0; i < checks.length; i++) {
		if (checks[i].checked) {
			if (j2 != 0) {
				s += ",";
			}
			s += checks[i].value;
			j2++;
		}
	}
	if (j1 + j2 == 0) {
		return true;
	}
	if (j1 == 0) {
		alert("please, select the cook");
		return true;
	}
	if (j2 == 0) {
		alert("It was soooo damn TASTY that even amazing chef " + radios[j1].value + " hadn't eaten it!\nAm I right?");
		return true;
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