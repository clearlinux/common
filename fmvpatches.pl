#!/usr/bin/perl
#
# fmvpatches.pl - part of common developer tooling
#
# Copyright 2016-2017 Intel Corporation
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

my %f;
my $fmv = {};
my $pkg = @ARGV[0];
my $path = "/var/lib/mock/clear-$pkg/root/builddir/build/BUILD/";

sub patch_function {
    my $avx2 = '__attribute__((target_clones("avx2","arch=atom","default")))'."\n";
    my ($file,@patch_line) = @_;
    my $dir = $pkg;

    my $patch_file = (split('/',$file))[-1];
    if ($file =~ /$path/p) {
        $dir = ${^POSTMATCH};
        if ($dir =~ /$patch_file/p) {
            $dir = ${^PREMATCH};
        }
    }

    print "patching $file @ lines \(@patch_line\)\n";
    open(my $in, "<", $file) or die "$! - $file\n";
    `mkdir -p results/patches/$dir`;
    open(my $out, ">","results/patches/$dir/$patch_file~") or die __LINE__," - $!\n";

    foreach (@patch_line) {
        my $line_num =  $_;

        while( <$in> ) {
            print $out $_;
            last if $. == ($line_num - 1);
        }

        print $out $avx2;
    }
    while( <$in> ) {
        print $out $_;
    }

    close $out;
    close $in;

    my $diff = `cd results/patches/; diff -su $file $dir$patch_file~`;
    open (my $d,">","results/patches/$dir$patch_file.patch") or die __LINE__," - $!\n";
    print $d $diff;
    close($d);
    `rm results/patches/$dir$patch_file~`;
    `sed -i 's|$path||' results/patches/$dir$patch_file.patch\n`;
}
sub find_file {
    my ($file) = @_;

    if ($file =~ /.*(\.\.\/)/p) {
	$file = ${^POSTMATCH};
    }

    my $n = (split('/',$file))[-1];
    chomp (my @matches = `find $path -iname $n`);

    foreach (@matches) {
        if ($_ =~ $n) {
            $file = $_;
        }
    }
    return $file;
}

open(BUILD_LOG, '<', "results/build.log") or die $!;
while (<BUILD_LOG>) {
    if($_ =~ /(\S+):([0-9]*):([0-9]*): note: (basic block|loop) (vectorized)/) {
	$fmv->{s_name} = (split('/',$1))[-1];
	$fmv->{f_name} = $1;
	push @{$f{$1}->{v_line}},$2;
    }
}
close(BUILD_LOG);

foreach (keys %f) {
    my $fname = $_;
    my @flines = @{$f{$_}->{v_line}};

    if ($fname =~ /(\.c$)/) {
        my $f_path = &find_file($fname);

        my @keys = 0;
        my $i = 0;
        foreach (`ctags --c-kinds=f -x $f_path`) {
            chomp $_;
            $keys[$i++] = (split(/\s+/,$_))[2]; # get function number line
        }
        @keys = sort {$a <=> $b} @keys;

        my @match_line = 0;
        # foreach line vectorized look for its closest function
        foreach my $i ( 0 .. $#flines ) {
            foreach (@keys) {
            if ($_ < $flines[$i] ) {
                $match_line[$i] = $_;
            }
            }
        }

        my %h;
        foreach (@match_line) {$h{$_} = $_;} @match_line = keys %h;
        @match_line = sort {$a <=> $b} @match_line;

        &patch_function($f_path,@match_line);
    }
}
