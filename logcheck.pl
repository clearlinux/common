#!/usr/bin/perl
#
# logcheck.pl - part of common developer tooling
#
# Copyright 2014-2017 Intel Corporation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

use File::Basename;


my %whitelist;
my %blacklist;
my $count = 0;

sub setup_whitelist
{
        my $count = 0;
        open(FILE, "../../projects/common/configure_whitelist") || return 0;
        while (<FILE>) {
                my $line = $_;
                chomp($line);

                $whitelist{$line} = $line;
                $count += 1;
        }
        close(FILE);
}

sub setup_blacklist
{
        my $count = 0;
        open(FILE, "../../projects/common/configure_blacklist") || return 0;
        while (<FILE>) {
                my $line = $_;
                chomp($line);

                $blacklist{$line} = $line;
                $count += 1;
        }
        close(FILE);
}

sub print_fatal
{
        my $pr = shift;
        print "[\033[1m\033[91mFATAL\033[0m] ". $pr . "\n"
}

setup_whitelist();
setup_blacklist();

while (<>) {
  my $line = $_;
  my $match;
  
  $match = "";
  if ($line =~ /^checking (.*)\.\.\. no/) {
      $match = $1;
  }
  if ($line =~ /^checking for (.*)\.\.\. no/) {
      $match = $1;
  }
  if ($line =~ /none required/) {
      $match = "";
  }
  if ($line =~ /warning: format not a string literal/) {
    $match = $line;
  }
  if ($match eq "") {
    next;
  }
  
  if (defined($whitelist{$match})) {
     # whitelisted
  } elsif (defined($blacklist{$match})) {
     print_fatal("Blacklisted configure-miss is forbidden: $match\n");
     exit 1;
  } else { 
     print "Configure miss: $match\n";
  }
}
