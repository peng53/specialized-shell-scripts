#/bin/perl

use strict;
use warnings;

require '../failure/pl/dqueue.pl';
require './yt_dl_g.pl';

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
	my $url = shift;
	my $vid = shift;
	my $vres = $ENV{'quality'} // 240;
	my $vfmt = $ENV{'vfmt'} // 'webm';
	my $abit = $ENV{'abr'} // 80;
	my $ytLines = YT_DL_G::ytFormats($url);

	$vres = YT_DL_G::hasRes($ytLines, $vres, $vfmt);
	$abit = YT_DL_G::closeABR($ytLines, $abit);

	if (length $vres == 0 or length $abit == 0) {
		print "Requested res/bitrate not available.\n";
		return;
	}

	ytdl_get((
		speed => '64K',
		fcode => $vres,
		url => $url,
		out => $vid
	));
	print "Waiting 10 secs to download audio..\n";
	sleep 10;
	ytdl_get((
		speed => '32K',
		fcode => $abit,
		url => $url,
		out => $vid.'aud'
	));
	return $vid;
}

sub streamlink_get {
	my $url = shift;
	my $vid = shift;
	my $res = $ENV{'quality'}.'p' // '240p';
	print "Downloading with streamlink\n";
	system("streamlink $url $res -o $vid >> ${outd}out.log 2>&1 &");
	return $vid;
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

sub deleteCached {
	# Deletes vid (& audio) if it exists
	my $vid = shift;
	if (-e $vid) {
		unlink($vid);
		unlink($vid.'aud') if -e $vid.'aud';
	}
	return $vid;
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
	} elsif ($cmd eq 'see') {
		print join("\n", @{DQueue::readOut(\%dhash)}), "\n";
	} elsif ($cmd eq 'go') {
		my $url = shift // nextu(\%dhash);
		my $vid;
		if ($url eq 'r'){
			$url = shift // nextu(\%dhash);
			$vid = $outd.$dhash{'cvid'};
			print "Resuming download..\n";
		} else {
			$vid = deleteCached(nextVid(\%dhash));
		}
		my $dl;
		if ($url =~ /\.youtube\.com/){
			$dl = ytdl_dash($url, $vid)
		} elsif ($url =~ /\.crunchyroll\.com/){
			$dl = streamlink_get($url, $vid);
		}
		print "Waiting 10 secs to play..\n";
		sleep 10;
		view($vid) if $dl;
	}
	untie %dhash;
}

unless (caller) {
	main(@ARGV);
}
