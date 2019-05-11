#/bin/perl

use strict;
use warnings;

require '../failure/pl/dqueue.pl';

package FQ;

our $outd = '/mnt/ramdisk/';
our $qfile = $outd.'q.dbm';
our @yt_args = qw(--no-part --youtube-skip-dash-manifest --no-call-home --no-playlist --no-progress);
our @player_args= qw(--pause --keep-open --really-quiet);
our $MVID = 5;

sub view {
	my $vid = shift;
	my $dash = ( -e $vid.'aud' ) ? "--audio-file=${vid}aud" : '';
	system("mpv @player_args $vid $dash &");
}

sub ytdl_get {
	my %args = @_;
	print "Downloading at quality = $args{fcode}, speed $args{speed}\n";
	system("youtube-dl @yt_args -r $args{speed} -f $args{fcode} -o $args{out} $args{url} >> ${outd}out.log 2>&1 &");
}

sub ytdl_dash {
	my $url = shift or die 'Need URL!';
	my $vid = shift or die 'Need output file!';
	ytdl_get((
		speed => '32K',
		fcode => '242',
		url => $url,
		out => $vid
	));
	print "Waiting 10 secs to download audio..\n";
	sleep 10;
	ytdl_get((
		speed => '32K',
		fcode => '250',
		url => $url,
		out => $vid.'aud'
	));
	print "Waiting 20 secs to play..\n";
	sleep 20;
	view($vid);
}

sub add {
	my $hash = shift;
	my $url = shift or die 'No Url Arg Given.';
	my $old = DQueue::add($hash,$url);
	print "Overwritten: $old\n" if $old;
	print "Added url: $url\n";
}

sub nextu {
	my $hash = shift;
	my $url = DQueue::get($hash);
	DQueue::advanceRead($hash);
	print "$url\n";
	return $url;
}

sub initDBM {
	my $hash = shift;
	if (! keys %$hash) {
		DQueue::initDBM($hash);
		$$hash{'cvid'} = 0;
		$$hash{'mvid'} = $MVID;
	}
}

sub nextVid {
	my $hash = shift;
	my $vid = $$hash{'cvid'};
	($$hash{'cvid'} += 1) %= $$hash{'mvid'};
	return $outd.$vid;
}

sub main {
	my %dhash;
	DQueue::loadIt(\%dhash, $qfile);
	FQ::initDBM(\%dhash);
	my $cmd = shift or die 'No Cmd Arg Given.';
	if ($cmd eq 'add') {
		FQ::add(\%dhash,shift);
	} elsif ($cmd eq 'view') {
		view($outd.$dhash{'cvid'});
	} elsif ($cmd eq 'ytd') {
		my $url = shift // nextu(\%dhash);
		my $vid;
		if ($url eq 'r'){
			$url = shift // nextu(\%dhash);
			$vid = $outd.$dhash{'cvid'};
			print "Resuming download..\n";
		} else {
			$vid = nextVid(\%dhash);
			if (-e $vid) {
				unlink($vid);
				unlink($vid.'aud') if -e $vid.'aud';
			}
		}
		#$url //= nextu(\%dhash);
		ytdl_dash($url, $vid);
	} elsif ($cmd eq 'see') {
		CORE::say join("\n", @{DQueue::readOut(\%dhash)});
	} elsif ($cmd eq 'qua') {
		print "$ENV{'quality'} $ENV{'speed'} $ENV{'aquality'}\n";
	}
	untie %dhash;
}

unless (caller) {
	main(@ARGV);
}
