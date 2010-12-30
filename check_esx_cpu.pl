#!/usr/bin/perl

# Perform CPU health checks on a VMWare ESX(i) host
# v1, sschneid@gmail.com

# From http://github.com/sschneid/misc/blob/master/nagios/plugins/check_esx_cpu
# Fixed about exit code  
# by Yusaku ONO

package check_esx_cpu;

use Getopt::Long;
use VMware::VIRuntime;

use strict;


my %exit_codes = ('UNKNOWN' ,-1,
                  'OK'      , 0,
                  'WARNING' , 1,
                  'CRITICAL', 2,);

my $self = check_esx_cpu->init();

my $view = Vim::find_entity_view( view_type => 'HostSystem' );

my ( $cpu );

$cpu->{'use'}   = $view->summary->quickStats->overallCpuUsage;
$cpu->{'total'} = $view->hardware->cpuInfo->hz / 1000000 * $view->hardware->
cpuInfo->numCpuThreads;

$cpu->{'utilization'} = ( $cpu->{'use'} / $cpu->{'total'} ) * 200;

Util::disconnect();

my ( $status );

if ( $cpu->{'utilization'} > $self->{'var'}->{'warn'} ) {
    $status = 'WARNING';
}

if ( $cpu->{'utilization'} > $self->{'var'}->{'crit'} ) {
    $status = 'CRITICAL';
}

$status ||= 'OK';

printf ( "CPU $status - used = %.2f%", $cpu->{'utilization'} );

if ( $self->{'var'}->{'perfdata'} ) {
    print ' | ';
    print 'cpu=' . $cpu->{'use'};
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
        )
    ) {
        $self->{'var'}->{'help'} = 1;
    }

    if ( $self->{'var'}->{'help'} ) {
        print qq(Type 'perldoc $0' for more options and information\n\n);
        print qq(USAGE: $0 -h <host> -u <user> -p <pass> -w <warn> -c <crit> );
        print qq([option]...\n);
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