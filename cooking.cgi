#!/usr/bin/perl

use strict;
use warnings;
use UTF8;

use Template;
use CGI;
use DBI;


our $result = main();

our $tpl = new Template({
	INCLUDE_PATH=>'/var/www/cgi-bin'
});
our $vars={
	title    => 'Cook helper',
	errors   => $result->{'errors'},
	messages => $result->{'messages'},
	log      => $result->{'log'},
	people   => $result->{'data'},
};

print "Content-type: text/html\n\n";
$tpl->process("cooking.tpl", $vars);

sub main {
	my $result = {};
	$result->{'errors'} = [];
	$result->{'messages'} = [];
	$result->{'log'} = [];
	$result->{'data'} = {};

	my $dsn = "DBI:mysql:database=stat_cooking;host=127.0.0.1;port=3306";
	my $dbh = DBI->connect($dsn, 'root')
	or push(@{$result->{'errors'} }, "Can't connect to MySQL server: $DBI::errstr")
	and return $result;
	
	my $event = get_param('event');
	$event ||= '';
	if ($event eq 'cooked') {
		return do_cook($result, $dbh);
	}
	if ($event eq 'register') {
		return do_registration($result, $dbh);
	}
	if ($event eq 'cancel') {
		return do_cancel($result, $dbh);
	}
	if ($event eq 'clearstats') {
		return do_clearstats($result, $dbh);
	}
	
	my $sth = $dbh->prepare("
		select 
			name,
			cooked,
			eaten,
			fed,
			ratio
		from 
			People
	");
	$sth->execute()
	or push(@{$result->{'errors'} }, "Can't do select of MySQL server: $DBI::errstr")
	and return $result;

	while (my($name, $cooked, $eaten, $fed, $ratio) = $sth->fetchrow_array() ) {
		$result->{'data'}->{$name}->{'ratio'} = $ratio;
		$result->{'data'}->{$name}->{'cooked'} = $cooked;
		$result->{'data'}->{$name}->{'eaten'} = $eaten;
		$result->{'data'}->{$name}->{'fed'} = $fed;
	}


	$sth = $dbh->prepare("
		select 
			id,
			cook,
			mouths,
			time
		from 
			Log
	");
	$sth->execute()
	or push(@{$result->{'errors'} }, "Can't do select log of MySQL server: $DBI::errstr")
	and return $result;

	while (my($id, $cook, $mouths, $time) = $sth->fetchrow_array() ) {
		$result->{'log'}->{$id}->{'time'} = $time;
		$result->{'log'}->{$id}->{'cook'} = $cook;
		$result->{'log'}->{$id}->{'mouths'} = $mouths;
	}

	return $result;
}

sub do_clearstats {
	my $result = shift;
	my $dbh = shift;

	$dbh->do("
		delete
		from
			People
	")
	or push(@{$result->{'errors'} }, "Can't do update of MySQL server: $DBI::errstr")
	and return $result;

	redirect();
	return $result;
}

sub do_cancel {
	my $result = shift;
	my $dbh = shift;

	my $id = get_param('id');
	my $sth = $dbh->prepare("
		select 
			cook,
			mouths
		from 
			Log
		where 
			id = $id
	");
	$sth->execute()
	or push(@{$result->{'errors'} }, "Can't do select log of MySQL server: $DBI::errstr")
	and return $result;
	$dbh->do("
		delete 
		from 
			Log
		where 
			id = $id
	")
	or push(@{$result->{'errors'} }, "Can't do delete from log of MySQL server: $DBI::errstr")
	and return $result;

	my($cook, $mouths) = $sth->fetchrow_array();
	my @mouths = split(',', $mouths);
	my $n = scalar(@mouths);
	my $k = 1.0 / $n;
	my @mouths_quoted;
	push(@mouths_quoted, $_) foreach @mouths;
	$mouths = '(' . join(', ', @mouths_quoted) . ')';
	$dbh->do("
		update 
			People
		set 
			ratio = ratio - 1,
			cooked = cooked - 1,
			fed = fed - $n
		where
			name='$cook'
	")
	or push(@{$result->{'errors'} }, "Can't do update of MySQL server: $DBI::errstr")
	and return $result;
	$dbh->do("
		update 
			People
		set 
			ratio = ratio + $k,
			eated = eated - 1
		where
			name in $mouths
	")
	or push(@{$result->{'errors'} }, "Can't do update of MySQL server: $DBI::errstr")
	and return $result;
	
	push(@{$result->{'messages'} }, "Event has been canceled");

	redirect();
	return $result;
}

sub do_cook {
	my $result = shift;
	my $dbh = shift;

	my $sth = $dbh->prepare("
		select 
			name
		from 
			People
	");
	$sth->execute()
	or push(@{$result->{'errors'} }, "Can't do select of MySQL server: $DBI::errstr")
	and return $result;

	my @names = ();
	while (my $name = $sth->fetchrow_array() ) {
		push(@names, $name);
	}

	my $cooker = get_param("cook");
	my @eats = split(',', get_param("mouths"));
	my $n = scalar(@eats);
	if ($n == 0) {
		push(@{$result->{'errors'} }, "Nobody eated O_o?!");
		return $result;
	}
	my $k = 1.0 / $n;
	
	#push(@{$result->{'errors'} }, "update People set ratio = ratio + 1, cooked = cooked + 1, fed = fed + $n where name='$cooker'");
	$dbh->do("
		update 
			People
		set 
			ratio = ratio + 1,
			cooked = cooked + 1,
			fed = fed + $n
		where
			name='$cooker'
	")
	or push(@{$result->{'errors'} }, "Can't do update of MySQL server: $DBI::errstr")
	and return $result;
	

	foreach my $eater (@eats) {
		#push(@{$result->{'errors'} }, "update People set ratio = ratio - $k, eaten = eaten + 1, where name='$eater'");
		$dbh->do("
			update 
				People
			set 
				ratio = ratio - $k,
				eaten = eaten + 1
			where
				name='$eater'
		")
		or push(@{$result->{'errors'} }, "Can't do update of MySQL server: $DBI::errstr")
		and return $result;
	}

	push(@{$result->{'messages'} }, "Cooking detected!");

	redirect();
	return $result;
}

sub do_registration {
	my $result = shift;
	my $dbh = shift;

	my $name = get_param('name');
	if (my $er = bad_name($name, $dbh)) {
		push(@{$result->{'errors'} }, "Can't register name '$name': $er");
	}

	$dbh->do("
		insert 
			People
		set
			name='$name'
	")
	or push(@{$result->{'errors'} }, "Can't do insert to MySQL server: $DBI::errstr")
	and return $result;

	push(@{$result->{'messages'} }, "$name has been registered");
	
	redirect();
	return $result;
}

sub redirect {
	my ($url) = ($0 =~ m@/([^/]*)$@);

	print CGI::redirect($url);
	exit(0);
}

sub bad_name {
	my $name = shift;
	return "The name is NULL" if $name eq '';
	
	return 0;
}

# обёртка для CGI::param - требует скалярный контекст
sub get_param {
	my $key = shift;

	return scalar(CGI::param($key));
}
