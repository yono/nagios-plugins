#!/usr/bin/perl

# Perform memory health checks on a VMWare ESX(i) host
# v1, sschneid@gmail.com

# From http://github.com/sschneid/misc/blob/master/nagios/plugins/check_esx_disk
# Fixed about exit code  
# by Yusaku ONO

package check_esx_disk;

use Getopt::Long;
use VMware::VIRuntime;

use strict;

my %exit_codes = ('UNKNOWN' ,-1,
                  'OK'      , 0,
                  'WARNING' , 1,
                  'CRITICAL', 2,);

my $self = check_esx_disk->init();

my $view = Vim::find_entity_view( view_type => 'HostSystem' );

my ( $disk );

foreach my $ref_store ( @{$view->datastore} ) {
    my $store = Vim::get_view( mo_ref => $ref_store );

    next unless $store->summary->name eq $ARGV[0];

    $disk->{'use'} = $store->summary->capacity - $store->summary->freeSpace;
    $disk->{'total'} = $store->summary->capacity;
    $disk->{'utilization'} = ( $disk->{'use'} / $disk->{'total'} ) * 100;
}

Util::disconnect();

my ( $status );

if ( $disk->{'utilization'} > $self->{'var'}->{'warn'} ) {
    $status = 'WARNING';
}

if ( $disk->{'utilization'} > $self->{'var'}->{'crit'} ) {
    $status = 'CRITICAL';
}

$status ||= 'OK';

printf ( "DISK $status - used = %.2f%", $disk->{'utilization'} );

if ( $self->{'var'}->{'perfdata'} ) {
    print ' | ';
    print 'used=' . $disk->{'use'};
}

print "\n";
exit $exit_codes{$status};

sub init {
    my $self = bless {}, shift;

    $self->GetOptions(
        'host|hostname=s' => \$self->{'var'}->{'hostname'},
        'username|u=s'    => \$self->{'var'}->{'username'},
        'password|p=s'    => \$self->{'var'}->{'password'},

        'warning=s'       => \$self->{'var'}->{'warn'},
        'critical=s'      => \$self->{'var'}->{'crit'},
        'perfdata|f'      => \$self->{'var'}->{'perfdata'}
    ) || { $self->{'var'}->{'help'} = 1 };

    unless (
        (
            $self->{'var'}->{'hostname'} &&
            $self->{'var'}->{'username'} &&
            $self->{'var'}->{'password'}
        ) &&
        (
            $self->{'var'}->{'warn'} &&
            $self->{'var'}->{'crit'}
        ) &&
        (
            $ARGV[0]
        )
    ) {
        $self->{'var'}->{'help'} = 1;
    }

    if ( $self->{'var'}->{'help'} ) {
        print qq(Type 'perldoc $0' for more options and information\n\n);
        print qq(USAGE: $0 -h <host> -u <user> -p <pass> -w <warn> -c <crit> );
        print qq([option]... <datastore-name>\n);
        exit $exit_codes{'UNKNOWN'};
    }

    Util::connect(
        'https://' . $self->{'var'}->{'hostname'} . '/sdk/webService',
        $self->{'var'}->{'username'},
        $self->{'var'}->{'password'}
    );

    return $self;
}



1;