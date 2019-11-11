## PyStatusBar
Templating engine for text-based status bars. 


#### Running
Basic config: outputs data to stdout
`PYTHONPATH=/path/to/pystatusbar/.. python3 -m pystatusbar --config /path/to/pystatusbar/config_example.config`
More complete config: more modules, runs xmobar and shows data there
`PYTHONPATH=/path/to/pystatusbar/.. python3 -m pystatusbar --config /path/to/pystatusbar/config_bxpsd.config`


#### TODO
 - Add preprocessor module to config file. On first run, convert config file to a more
   native format (pickle?) and save that somewhere along with the config's checksum.
   This should speed up subsequent launches with the same config file.

