package core::task;

use Exporter;
use MooseX::Declare;
use Socket qw(inet_aton AF_INET);
use threads;

our @ISA = qw(Exporter);
our @EXPORT_OK = qw(execute);

# Base class for all tasks
class Task {
    use constant {
        TIMEOUT => 30,
        PARSE_FILES => 1
    };
    
    has "host" => (isa => "Str", is => "rw");
    has "ip" => (isa => "Str", is => "rw");
    has "proto" => (isa => "Str", is => "rw");
    has "port" => (isa => "Int", is => "rw");
    has "lang" => (isa => "Str", is => "rw");
    has "produced_output" => (isa => "Int", is => "rw", default => 0);
    has "_stop" => (isa => "Int", is => "rw", default => 0);
    has "_result" => (is => "rw");
    
    # Check if task is stopped
    method _check_stop {
        if ($self->_stop) {
            die "Task stopped.";
        }
    }
    
    # Write result to a file
    method _write_result(Str $str) {
        if ($self->_result) {
            print {$self->_result} $str . "\n";
        } else {
            print $str . "\n";
        }
    }
    
    # Parse input arguments
    method _parse_input {
        my @output_arguments;
        
        if (scalar(@ARGV) < 2) {
            die("At least 2 command line arguments should be specified.\n");
        }    

        # parse the first file with hostname or IP
        my ($fp, @lines);        
        open($fp, $ARGV[0]) or die("Unable to open target file: " . $ARGV[0] . ".\n");
        
        while (<$fp>) {
            chomp;
            push(@lines, $_);
        }
        
        close($fp);
        
        if (scalar(@lines) < 4) {
            die("Target file should contain at least 4 lines.\n");
        }
        
        unless ($lines[0]) {
            die("Target file should contain either host name or IP address of the target host on the 1st line.\n");
        }
        
        if ($lines[0] =~ /^\d+\.\d+\.\d+\.\d+$/) {
            $self->ip($lines[0]);
        } else {
            $self->host($lines[0]);
        }
        
        $self->proto($lines[1]);
        $self->port($lines[2] ? $lines[2] : 0);
        $self->lang($lines[3]);

        unless ($self->lang) {
            die("Target file should contain language name on the 4th line.\n");
        }

        # output file
        my $result_file;
        open($result_file, ">" . $ARGV[1]) or die("Unable to open result file: " . $ARGV[1] . ".\n");
        $self->_result($result_file);

        # parse the remaining arguments
        foreach my $arg (@ARGV[2, -1]) {
            unless ($arg) {
                next;
            }

            unless ($self->PARSE_FILES) {
                push(@output_arguments, $arg);
                next;
            }
            
            @lines = ();            
            open($fp, $arg) or die("Unable to open input file: $arg.\n");
            
            while (<$fp>) {
                chomp;
                push(@lines, $_);
            }
            
            close($fp);
            push(@output_arguments, @lines);            
        }

        return @output_arguments;
    }
    
    # Stop the task
    method stop {
        $self->_stop = 1;
    }
    
    # Run the task
    method run {
        eval {
            $SIG{"ALRM"} = sub {
                die("Task has timed out.\n");
            };

            my @arguments = $self->_parse_input();

            if ($self->TIMEOUT > 0) {
                alarm($self->TIMEOUT);
            }
                        
            $self->main(\@arguments);
        };

        alarm(0);

        if ($@) {
            my $error = $@;
            $self->_write_result($error);
        }
    }
}

# Executes task and controls its execution
sub execute {    
    my $obj = shift;
    
    if (!$obj || !$obj->isa("Task")) {
        die("Invalid task object.\n");
    }

    my $thread = async {
        $obj->run();
    };

    $SIG{"ALRM"} = sub {
        $thread->kill("ALRM");
    };

    while (1) {
        my @joinable = threads->list(threads::joinable);

        if (scalar(@joinable)) {
            $joinable[0]->join();
            last;
        }

        sleep(1);
    }
}

1;
