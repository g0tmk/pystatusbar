import logging
import time
import sys
import math
from multiprocessing import Process, Lock, Array, Event
from ctypes import c_char

from .configfile import ConfigFile, MINIMUM_UPDATE_RATE, ConfigParseError
from .status_modules import lookup_module
from .xmobar_runner import start_xmobar

if sys.version_info < (3, 6):
    print('This requires python 3.6+', file=sys.stderr)
    sys.exit(1)

_PROGRAM_NAME = "pystatusbar"
_VERSION = "0.0.0"
_START_TIMESTAMP = time.strftime("%y%m%d_%H%M%S")  # used in filenames

_MAX_STDIN_LINE_LEN = 300


class StdinGotEOF(Exception):
    pass

def run_startup_animation(output_filenames):

    with open(output_filenames[0], 'w') as handle:
        handle.write('')
    with open(output_filenames[2], 'w') as handle:
        handle.write('')


    def ease_in_out_cubic(t):
        if t < 0.5:
            return 4*t*t*t
        else:
            return (t-1)*(2*t-2)*(2*t-2)+1
    def ease_in_out_cubic_2(t):
        if t < 0.5:
            t = t * 2
            if t < 0.5:
                return 4*t*t*t
            else:
                return (t-1)*(2*t-2)*(2*t-2)+1
        else:
            t = (t-0.5) * 2
            t = 1 - t
            if t < 0.5:
                return 4*t*t*t
            else:
                return (t-1)*(2*t-2)*(2*t-2)+1

    canvas_width = 250
    bar_width = 10
    steps_in_animation = 1000
    time_per_step = 0.001

    empty_space = canvas_width - bar_width
    filled_space = canvas_width - empty_space

    for i in range(1000):
        current_time = i / steps_in_animation
        x_position = ease_in_out_cubic(current_time) * canvas_width

        left_empty_space = math.floor(x_position) - (bar_width // 2)

        right_empty_space = canvas_width - bar_width - left_empty_space

        time.sleep(time_per_step)

        bar = "{}{}{}".format(
            left_empty_space * " ",
            bar_width * "*",
            right_empty_space * " ")

        with open(output_filenames[1], 'w') as handle:
            handle.write(bar)

def setup_logging(verbose=False):
    filename = "/tmp/pystatusbar_debug_{}.log".format(_START_TIMESTAMP)

    # set up logging to file
    filehandler = logging.FileHandler(filename,
                                      mode="a",
                                      encoding="utf-8")
    filehandler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s, %(levelname)-8s, %(message)s",
                                  datefmt="%m-%d-%y %H:%M:%S")
    filehandler.setFormatter(formatter)

    console = logging.StreamHandler()
    if verbose:
        console.setLevel(logging.DEBUG)
    else:
        console.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s",
                                  datefmt="%H:%M:%S")
    console.setFormatter(formatter)

    logging.basicConfig(handlers=[filehandler, console],
        level=logging.DEBUG)

def format_stdin_line(line):
    #return "<raw={}:{}/>".format(len(line), line)
    return line

def output_status_once(config, output_filenames, cached_status_modules, stdin_value):
    for template, filename in [
            (config.align_left, output_filenames[0]),
            (config.align_center, output_filenames[1]),
            (config.align_right, output_filenames[2])]:
        output_string = template
        for identifier in config.get_identifiers_from_template_string(template):
            if identifier == "StdinReader":
                module_output = format_stdin_line(stdin_value)
            else:
                if identifier not in cached_status_modules:
                    module_type = config.get_module_type_by_identifier(identifier)
                    cached_status_modules[identifier] = lookup_module(module_type).from_config_dict(
                        config.get_config_dict_by_identifier(identifier))

                module_output = cached_status_modules[identifier].run_cached()

            output_string = output_string.replace(
                "{0}{1}{0}".format(
                    config.template_replace_character,
                    identifier),
                module_output)

        if filename:
            with open(filename, 'w') as handle:
                print(output_string, end="", file=handle)
        else:
            print(output_string)

def continually_output_status(most_recent_stdin_line, stdin_updated_lock, config, output_filenames, stop_worker_event):
    cached_status_modules = {}
    while not stop_worker_event.is_set():
        if stdin_updated_lock.acquire(timeout=3):
            stdin_value = most_recent_stdin_line.value.decode("utf-8")
            output_status_once(config, output_filenames, cached_status_modules, stdin_value)

def read_stdin_to_value(most_recent_stdin_line, stdin_updated_lock, stop_main_event, stop_worker_event):
    sys.stdin = open(0)

    while True:
        line = sys.stdin.readline()

        # exit program on EOF
        if line == '':
            stop_main_event.set()
            break

        # remove newline character from end, then trim to max line length
        line = line[:-1][:_MAX_STDIN_LINE_LEN]

        most_recent_stdin_line.value = bytes(line, encoding="utf-8")
        try:
            stdin_updated_lock.release()
        except ValueError:
            # if lock is already released it throws this error, which is OK
            pass

def main():
    import argparse

    p = argparse.ArgumentParser(prog=_PROGRAM_NAME,
                                description=("Templating engine for text-based status "
                                    "bars."))

    p.add_argument("-c", "--config",
                   type=argparse.FileType('r'),
                   help=("Path to config file."))

    p.add_argument("--xmobar",
                   action='store_true',
                   default=False,
                   help=("If true, run xmobar and output stats that way."))

    p.add_argument("--version",
                   action="version",
                   version="%(prog)s v{}".format(_VERSION))

    p.add_argument("--verbose",
                   default=False,
                   action="store_true",
                   help=("If set, show more log messages."))

    args = p.parse_args()

    setup_logging(verbose=args.verbose)
    logging.debug("Starting {} version: {}".format(_PROGRAM_NAME, _VERSION))

    config = ConfigFile(args.config)

    stop_main_event = Event()
    stop_worker_event = Event()
    stdin_updated_lock = Lock()
    # Make array 2x larger in case line is all unicode
    most_recent_stdin_line = Array(c_char, _MAX_STDIN_LINE_LEN*2)
    most_recent_stdin_line.value = bytes("default stdin value", encoding="utf-8")

    if config.output_program is not None:
        if config.output_program == 'xmobar':
            output_filenames = start_xmobar(stop_worker_event)
        elif config.output_program == 'none':
            pass
        else:
            raise ConfigParseError('Unrecognised output_program {}'.format(repr(config.output_program)))

    run_startup_animation(output_filenames)

    workers = [
    Process(target=continually_output_status, args=(
        most_recent_stdin_line,
        stdin_updated_lock,
        config, output_filenames,
        stop_worker_event,)),
    Process(target=read_stdin_to_value, args=(
        most_recent_stdin_line,
        stdin_updated_lock,
        stop_main_event,
        stop_worker_event,)),
    ]

    for w in workers:
        w.start()

    while not stop_main_event.is_set():
        time.sleep(1)
        try:
            stdin_updated_lock.release()
        except ValueError:
            pass

    stop_worker_event.set()

    for w in workers:
        w.join()

if __name__ == "__main__":
    main()

