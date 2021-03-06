# Apache Range
# ---
# [Author]
# Ryusuke Tsuda (InfoAlive Corp.)
# http://www.infoalive.com/

use MooseX::Declare;
use core::task qw(execute);

# Apache Range task
class Apache_Range extends Task {
    use LWP::UserAgent;

    # Make range header
    method _make_range_header(Int $range_count) {
        my $range_start = 1;
        my $range_end = 10;
        my @range_set;

        foreach my $i ( 1 .. $range_count ) {
            push(@range_set, $range_start . "-" . $range_end);
            $range_start = (10 * $i) + 1;
            $range_end = $range_start + 9;
        }

        my $range_str = "bytes=" . join(",", @range_set);
        return $range_str;
    }

    # Process host and range count
    method _process(Str $host, Str $proto, Int $range_count) {
        my $warn_range_count = 200;
        my $ua = LWP::UserAgent->new;
        my $url;

        unless ($proto) {
            $proto = "http";
        }

        $url = "$proto://$host";
        my $range = $self->_make_range_header($range_count);

        my $req = HTTP::Request->new(GET => $url);
        $req->header(Range => $range);
        my $res = $ua->request($req);

        if ($res->is_success) {
            my $content = $res->content;
            my $header = $res->header("Content-Range");

            unless ($header) {
                $header = "";
            }

            if ($header =~ /bytes/ && $range_count > $warn_range_count) {
                $self->_write_result("[Warning] Host can accept more than $warn_range_count ranges.\n");
            } elsif ($header =~ /bytes/ && $range_count <= $warn_range_count) {
                $self->_write_result("[Info] Host can accept $range_count range(s).\n");
            } else {
                $self->_write_result("[Info] Host ignored Range-Header.\n");
            }
        } else {
            $self->_write_result("[Info] HTTP request failed: " .$res->status_line."\n");
        }
    }

    # Main function
    method main($args) {
        $self->_process($self->target, $self->proto, $self->_get_arg_scalar($args, 0, 10));
    }

    # Test function
    method test {
        $self->_process("gtta.demo.stellarbit.com", "http", 10);
    }
}

execute(Apache_Range->new());
