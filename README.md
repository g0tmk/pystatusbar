## PyStatusBar
Templating engine for text-based status bars. 


#### Running
Basic config: outputs data to stdout

    PYTHONPATH=/path/to/pystatusbar/.. python3 -m pystatusbar --config /path/to/pystatusbar/config_example.config

More complete config: more modules, runs xmobar and shows data there

    PYTHONPATH=/path/to/pystatusbar/.. python3 -m pystatusbar --config /path/to/pystatusbar/config_bxpsd.config


#### TODO
 - When connected to vpn, network speed module does not show network traffic to devices
   on the local network. Should ignore a few devices, and total the rest, instead of 
   only showing traffic through the default device.
 - Add preprocessor module to config file. On first run, convert config file to a more
   native format (pickle?) and save that somewhere along with the config's checksum.
   This should speed up subsequent launches with the same config file.
 - Allow custom 'Network down' messages in Network config (and others)
 - Figure out why xmobar seems to occasionally blank for a frame.
   - Maybe the file is blank for some reason when read by xmobar. A more complicated
     command (compared to cat) could check if the file is empty, and if so, log it.
   - It seems to only happen to the left side.. maybe its just me. Could be an issue
     specifically with stdinreader.
 - (Future) Generate and handle Stdinreader contents completely inside pystatusbar. This
   will work around the limitations of xmonad's window title capability.
 - Generalize hiding functionality so it can be used for more tan just sensor thresholds.



