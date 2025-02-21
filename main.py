# Enviro - wireless environmental monitoring and logging
#
# On first run Enviro will go into provisioning mode where it appears
# as a wireless access point called "Enviro <board type> Setup". Connect
# to the access point with your phone, tablet or laptop and follow the
# on screen instructions.
#
# The provisioning process will generate a `config.py` file which 
# contains settings like your wifi username/password, how often you
# want to log data, and where to upload your data once it is collected.
#
# You can use enviro out of the box with the options that we supply
# or alternatively you can create your own firmware that behaves how
# you want it to - please share your setups with us! :-)
#
# Need help? check out https://pimoroni.com/enviro-guide
#
# Happy data hoarding folks,
#
#   - the Pimoroni pirate crew

# uncomment the below two lines to change the amount of logging enviro will do
# from phew import logging
# logging.disable_logging_types(logging.LOG_DEBUG)

# Issue #117 where neeed to sleep on startup otherwis emight not boot
from time import sleep
sleep(0.5)

# import enviro firmware, this will trigger provisioning if needed
import enviro
import os
from enviro import i2c

# pimoroni 1.12"
from sh1107 import SH1107_I2C
from ssd1327 import SSD1327_I2C

from writer import Writer
import courier20

from trackball import Trackball

try:
  # initialise enviro
  enviro.startup()

  trackball = Trackball( i2c )
  trackball.set_rgbw(0, 0, 128, 0)
  WIDTH = 128
  HEIGHT = 128
  BORDER = 2
  #oled3 = SH1107_I2C(WIDTH, HEIGHT, i2c, address=0x3C, rotate=0)
  oled3 = SSD1327_I2C(WIDTH, HEIGHT, i2c, addr=0x3D)
  oled3.fill(0)
  textWri = Writer(oled3, courier20)
  textWri.printstring(" Reading \n Sensors \n\n May Run \n  Pumps  ")
  oled3.show()
  # if the clock isn't set...
  if not enviro.is_clock_set():
    enviro.logging.info("> clock not set, synchronise from ntp server")
    if not enviro.sync_clock_from_ntp():
      # failed to talk to ntp server go back to sleep for another cycle
      enviro.halt("! failed to synchronise clock")  

  # check disk space...
  if enviro.low_disk_space():
    # less than 10% of diskspace left, this probably means cached results
    # are not getting uploaded so warn the user and halt with an error
    
    # Issue #126 to try and upload if disk space is low
    # is an upload destination set?
    if enviro.config.destination:
      enviro.logging.error("! low disk space. Attempting to upload file(s)")

      # if we have enough cached uploads...
      enviro.logging.info(f"> {enviro.cached_upload_count()} cache file(s) need uploading")
      if not enviro.upload_readings():
        enviro.halt("! reading upload failed")
    else:
      # no destination so go to sleep
      enviro.halt("! low disk space")
  
  # TODO this seems to be useful to keep around?
  filesystem_stats = os.statvfs(".")
  enviro.logging.debug(f"> {filesystem_stats[3]} blocks free out of {filesystem_stats[2]}")

  # TODO should the board auto take a reading when the timer has been set, or wait for the time?
  # take a reading from the onboard sensors
  enviro.logging.debug(f"> taking new reading")
  reading = enviro.get_sensor_readings()
  
  from enviro import config
  trackball.set_rgbw(0, 255, 0, 0)
  
  select = '!'
  edit = '>'
  mode_a = select
  mode_b = ' '
  mode_c = ' '
  was_clicked = False
  
  ignore = 5
  big_change = 15
  big_increment = 5
  small_increment = 1
  edit_loop = 45
  while edit_loop>0:
    edit_loop-=1
    up, down, left, right, switch, state = trackball.read()
    print("r:    {:02d}\tu:    {:02d}\td:    {:02d}\tl:     {:02d}\tswi:{:03d}\tsta:{}".format(right, up, down, left, switch, state))
    oled3.fill(0)
    Writer.set_textpos(oled3, 0 , 0)
    textWri.printstring(" LAST TGT \nA {:3}{:1}{:3}\n\nB {:3}{:1}{:3}\n\nC {:3}{:1}{:3}".format(reading.get("moisture_a"), mode_a, config.moisture_target_a,reading.get("moisture_b"), mode_b, config.moisture_target_b, reading.get("moisture_c"), mode_c, config.moisture_target_c))
    oled3.show()
    if state and not was_clicked:
        # clearing up/down so doesn't move/incrememt with click
        up = 0
        down = 0
        if mode_a == select:
            mode_a = edit
            trackball.set_rgbw(255,0,0,0)
        elif mode_b == select:
            mode_b = edit
            trackball.set_rgbw(255,0,0,0)
        elif mode_c == select:
            mode_c = edit
            trackball.set_rgbw(255,0,0,0)      
        elif mode_a == edit:
            mode_a = select
            trackball.set_rgbw(0,255,0,0)
        elif mode_b == edit:
            mode_b = select
            trackball.set_rgbw(0,255,0,0)
        elif mode_c == edit:
            mode_c = select
            trackball.set_rgbw(0,255,0,0)
        was_clicked = True
    elif not state and was_clicked:
        was_clicked = False

    if up > ignore:
        if mode_a == select:
            mode_c = select
            mode_a = ' '
        elif mode_b == select:
            mode_a = select
            mode_b = ' '
        elif mode_c == select:
            mode_b = select
            mode_c = ' '
        elif mode_a == edit:
            if up > big_change:
                config.moisture_target_a +=big_increment
            else:
                config.moisture_target_a +=small_increment
            if config.moisture_target_a >100:
                config.moisture_target_a = 100      
        elif mode_b == edit:
            if up > big_change:
                config.moisture_target_b +=big_increment
            else:
                config.moisture_target_b +=small_increment
            if config.moisture_target_b >100:
                config.moisture_target_b = 100      
        elif mode_c == edit:
            if up > big_change:
                config.moisture_target_c +=big_increment
            else:
                config.moisture_target_c +=small_increment
            if config.moisture_target_c >100:
                config.moisture_target_c = 100      
            
    elif down > ignore:
        if mode_a == select:
            mode_b = select
            mode_a = ' '
        elif mode_b == select:
            mode_c = select
            mode_b = ' '
        elif mode_c == select:
            mode_a = select
            mode_c = ' '
            
        elif mode_a == edit:
            if up > big_change:
                config.moisture_target_a -=big_increment
            else:
                config.moisture_target_a -=small_increment
            if config.moisture_target_a <0:
                config.moisture_target_a = 0
        elif mode_b == edit:
            if up > big_change:
                config.moisture_target_b -=big_increment
            else:
                config.moisture_target_b -=small_increment

            if config.moisture_target_b <0:
                config.moisture_target_b = 0            
        elif mode_c == edit:
            if up > big_change:
                config.moisture_target_c -=big_increment
            else:
                config.moisture_target_c -=small_increment

            if config.moisture_target_c <0:
                config.moisture_target_c = 0
    #sleep(0.1)
  trackball.set_rgbw(0,0,255,0)

  # here you can customise the sensor readings by adding extra information
  # or removing readings that you don't want, for example:
  # 
  #   del readings["temperature"]        # remove the temperature reading
  #
  #   readings["custom"] = my_reading()  # add my custom reading value

  # is an upload destination set?
  if enviro.config.destination:
    # if so cache this reading for upload later
    enviro.logging.debug(f"> caching reading for upload")
    enviro.cache_upload(reading)

    # if we have enough cached uploads...
    if enviro.is_upload_needed():
      enviro.logging.info(f"> {enviro.cached_upload_count()} cache file(s) need uploading")
      if not enviro.upload_readings():
        enviro.halt("! reading upload failed")
    else:
      enviro.logging.info(f"> {enviro.cached_upload_count()} cache file(s) not being uploaded. Waiting until there are {enviro.config.upload_frequency} file(s)")
  else:
    # otherwise save reading to local csv file (look in "/readings")
    enviro.logging.debug(f"> saving reading locally")
    enviro.save_reading(reading)

  # go to sleep until our next scheduled reading
  enviro.sleep()

# handle any unexpected exception that has occurred
except Exception as exc:
  enviro.exception(exc)
