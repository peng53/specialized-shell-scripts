#/bin/perl

use strict;
use warnings;

require '../failure/pl/dqueue.pl';

package FQ;

our $outd = '/mnt/ramdisk/';
our $qfile = $outd.'q.dbm';
our $yt_args = '--no-part --youtube-skip-dash-manifest --no-call-home --no-playlist';

sub ytdl_get {
	my %args = @_;
	print `echo youtube-dl $yt_args -r $args{speed} -f $args{fcode} $args{url} -o $args{out} &`;
}

sub ytdl_dash {
	my $url = shift;
	ytdl_get((
		speed => '32K',
		fcode => '242',
		url => $url,
		out => $outd.'1'
	));
	sleep 10;
	$yt_args .= ' -q';
	ytdl_get((
		speed => '32K',
		fcode => '250',
		url => $url,
		out => $outd.'1aud'
	));
}

sub add {
	my $url = shift;

}

sub main {
	ytdl_dash('testtube');
}

unless (caller) {
	main(@ARGV);
}
