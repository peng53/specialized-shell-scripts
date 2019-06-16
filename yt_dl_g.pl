#!/bin/perl
use strict;
use warnings;

package YT_DL_G;

sub ytFormats {
	# Gets all possible formats for an url.
	my $url = shift or die 'Need Url to process';
	my @lines = `youtube-dl -F $url 2>/dev/null`;
	return \@lines;
}

sub closeABR {
	# Assumes output orders audio formats in bitrate ascending..
	my $lines = shift or die 'Need lines to process';
	my $abr = shift or die 'Need ABR to check';
	my $best = '';
	foreach (@$lines) {
		if (/^(\w+).+DASH audio\s+(\w+)k/) {
			return $best if $2>$abr;
			$best = $1;
		}
	}
	return $best;
}

sub hasRes {
	# Will only return exact match.
	my $lines = shift or die 'Need lines to process';
	my $res = shift or die 'Need RES to check';
	my $fmt = shift // 'mp4';
	foreach (@$lines) {
		return $1 if /^(\w+)\s+\Q$fmt\E\s+\w+\s+\Q$res\Ep/;
	}
	return '';
}

unless (caller) {
	my $url = shift or die 'No url was given.';
	my $lines = ytFormats($url);
	# Defaults unless 'res fmt abr' are given.
	# Only takes that order.
	my $res = shift // 240;
	my $fmt = shift // 'mp4';
	my $abr = shift // 90;
	print "Resolution ${res}p as ${fmt}:", hasRes($lines, $res, $fmt), "\n";
	print "Audio was bitrate of <${abr}:", closeABR($lines, $abr), "\n";
}
