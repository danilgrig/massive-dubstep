#!/usr/bin/perl

use strict;
use warnings;

use Template;
use CGI;
use DBI;

open(LOG, ">>/var/www/cgi-bin/log.txt");

our $result = main();

our $tpl = new Template({
	INCLUDE_PATH=>'/var/www/cgi-bin'
});
our $vars={
	title        => 'Cook helper',
	errors       => $result->{'errors'},
	messages     => $result->{'messages'},
	old_messages => $result->{'old_messages'},
	log          => $result->{'log'},
	people       => $result->{'data'},
};

print "Content-type: text/html\n\n";
$tpl->process("cooking.tpl", $vars);

sub main {
	my $result = {};
	$result->{'errors'} = [];
	$result->{'old_messages'} = [];
	$result->{'messages'} = [];
	$result->{'log'} = {};
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
	if ($event eq 'delete') {
		return do_delete($result, $dbh);
	}
	if ($event eq 'restore') {
		return do_restore($result, $dbh);
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
		$result->{'data'}->{$name}->{'ratio'} = sprintf("%.2f", $ratio);
		$result->{'data'}->{$name}->{'cooked'} = $cooked;
		$result->{'data'}->{$name}->{'eaten'} = $eaten;
		$result->{'data'}->{$name}->{'fed'} = $fed;
	}


	$sth = $dbh->prepare("
		select 
			id,
			cook,
			mouths,
			time,
			status
		from 
			Log
	");
	$sth->execute()
	or push(@{$result->{'errors'} }, "Can't do select log of MySQL server: $DBI::errstr")
	and return $result;

	while (my($id, $cook, $mouths, $time, $status) = $sth->fetchrow_array() ) {
		$result->{'log'}->{$id}->{'time'} = $time;
		$result->{'log'}->{$id}->{'cook'} = $cook;
		$result->{'log'}->{$id}->{'status'} = $status;
		@{$result->{'log'}->{$id}->{'mouths'} } = split(',', $mouths);
	}

	my $msg = get_param('msg');
	if ($msg) {
		push(@{$result->{'old_messages'} }, $_) foreach split(',', $msg);
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

	push(@{$result->{'messages'} }, "Clearstats! YES!!!");
	
	redirect($result);
	return $result;
}

sub do_delete {
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
		and
			status = 1
	");
	$sth->execute()
	or push(@{$result->{'errors'} }, "Can't do select log of MySQL server: $DBI::errstr")
	and return $result;

	my($cook, $mouths) = $sth->fetchrow_array();
	unless ($cook){
		push(@{$result->{'errors'} }, "It havn't happened!");
		return $result;
	}

	update_score($result, $dbh, $cook, $mouths, '-')
	or return $result;

	$dbh->do("
		update
			Log
		set
			status = 2
		where
			id = $id
	")
	or push(@{$result->{'errors'} }, "Can't do update Logr: $DBI::errstr")
	and return $result;
	
	push(@{$result->{'messages'} }, "Event has been deleted");

	redirect($result);
	return $result;
}

sub do_restore {
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
		and
			status = 2
	");
	$sth->execute()
	or push(@{$result->{'errors'} }, "Can't do select log of MySQL server: $DBI::errstr")
	and return $result;

	my($cook, $mouths) = $sth->fetchrow_array();
	unless ($cook){
		push(@{$result->{'errors'} }, "It havn't happened!");
		return $result;
	}

	update_score($result, $dbh, $cook, $mouths, '+')
	or return $result;

	$dbh->do("
		update
			Log
		set
			status = 1
		where
			id = $id
	")
	or push(@{$result->{'errors'} }, "Can't do update Logr: $DBI::errstr")
	and return $result;
	
	push(@{$result->{'messages'} }, "Event has been restored");

	redirect($result);
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

	my $cook = get_param("cook");
	my $mouths = get_param("mouths");
	update_score($result, $dbh, $cook, $mouths, '+')
	or return $result;

	$dbh->do("
		insert
			Log
		set 
			cook = '$cook',
			mouths = '$mouths'
	")
	or push(@{$result->{'errors'} }, "Can't insert into Log: $DBI::errstr")
	and return $result;

	push(@{$result->{'messages'} }, "Cooking detected!");

	redirect($result);
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
	
	redirect($result);
	return $result;
}

sub redirect {
	my $result = shift;

	my ($url) = ($0 =~ m@/([^/]*)$@);
	$url .= '?msg=' . join(',', @{$result->{'messages'} }) if $result->{'messages'};

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

sub update_score {
	my $result = shift;
	my $dbh = shift;
	my $cook = shift;
	my $mouths = shift;
	my $sign = shift;

	my $nsign = $sign eq '+' ? '-' : '+';
	my @eats = split(',', $mouths);
	my $n = scalar(@eats);
	if ($n == 0) {
		push(@{$result->{'errors'} }, "Nobody eated O_o?!");
		return 0;
	}
	my $k = 1.0 / $n;
	
	$dbh->do("
		update 
			People
		set 
			ratio = ratio $sign 1,
			cooked = cooked $sign 1,
			fed = fed $sign $n
		where
			name='$cook'
	")
	or push(@{$result->{'errors'} }, "Can't do update of MySQL server: $DBI::errstr")
	and return 0;
	

	foreach my $eater (@eats) {
		$dbh->do("
			update 
				People
			set 
				ratio = ratio $nsign $k,
				eaten = eaten $sign 1
			where
				name='$eater'
		")
		or push(@{$result->{'errors'} }, "Can't do update of MySQL server: $DBI::errstr")
		and return 0;
	}
	
	return 1;
}