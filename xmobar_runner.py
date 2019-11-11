import subprocess
import time
from multiprocessing import Process

_xmobar_left_output_file = '/tmp/left_pystatusbar_output'
_xmobar_center_output_file = '/tmp/center_pystatusbar_output'
_xmobar_right_output_file = '/tmp/right_pystatusbar_output'

_xmobar_config_filename = '/tmp/pystatusbar_xmobar_config'

_xmobar_config_template = """
-- from http://beginners-guide-to-xmonad.readthedocs.io/configure_xmobar.html

Config { font = "xft:envypn:pixelsize=13:style=Regular"
        , additionalFonts = ["xft:FontAwesome:size=8", "xft:FontAwesome:size=10"]
        , borderColor = "black"
        , borderWidth = 0
        , border = TopB
        , bgColor = "black"
        , alpha = 242
        , fgColor = "grey"

        -- settings for top-bar-mode
        , position = TopW L 100

        -- settings for bottom-bar-mode
        --, textOffset = 14
        --, position = BottomW L 100
        --, iconOffset = 9

        , iconRoot = "/home/g0tmk/.xmonad/resources" -- default: "."
        , commands = 
                [ 
                  Run Com "cat"
                                     [ "<left_filename>"
                                     ] "left" 1
                , Run Com "cat"
                                     [ "<center_filename>"
                                     ] "center" 1
                , Run Com "cat"
                                     [ "<right_filename>"
                                     ] "right" 1
                , Run StdinReader
                ]
        , sepChar = "%"
        , alignSep = "}{"
        , template = "%left%}%center%{%right%"
        }

"""

def xmobar_runner(config_filename, left_filename, center_filename, right_filename, stop_event):
    template = _xmobar_config_template[:]
    template = template.replace('<left_filename>', left_filename)
    template = template.replace('<center_filename>', center_filename)
    template = template.replace('<right_filename>', right_filename)

    with open(_xmobar_config_filename, 'w') as handle:
        handle.write(template)

    p = subprocess.Popen(['xmobar', config_filename])

    while p.poll() is None:
        time.sleep(1)
        if stop_event.is_set():
            p.kill()
            break

def start_xmobar(worker_stop_event):
    Process(target=xmobar_runner, args=(
        _xmobar_config_filename,
        _xmobar_left_output_file,
        _xmobar_center_output_file,
        _xmobar_right_output_file,
        worker_stop_event
        )).start()

    return (
        _xmobar_left_output_file,
        _xmobar_center_output_file,
        _xmobar_right_output_file
    )



    