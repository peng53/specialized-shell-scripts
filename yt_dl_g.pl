#!/bin/perl

use strict;
use warnings;

#my $url=shift;
## lines are lines output by calling `youtube-dl -F $url`
## its using 't' ATM which should cache from the above cmd
## for testing
my @lines = `cat /mnt/ramdisk/t`;
#print @lines;
my $fmt = shift or die;
my $res = shift or die;
my $abr = shift or die;
foreach (@lines) {
	chomp;
	print $_, "\n" if /\Q$fmt\E\s+\d+x\d+\s+\Q$res\Ep/;
	print $_, "\n" if /DASH audio\s+\Q$abr\Ek/;
	#DASH audio[[:space:]]+${abr}k" t

}
