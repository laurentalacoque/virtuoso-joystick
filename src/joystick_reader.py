#!/usr/bin/python

import sys
import struct
import time
from threading import Event, Thread
from Queue import Queue, Empty

import logging
log = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/js.log",level=logging.DEBUG)

infile_path = "/dev/input/js0"
wait_secs = 0.05
EVENT_SIZE = struct.calcsize("IhBB")

in_queue = Queue() # cadence to script
out_queue = Queue() # script to cadence
ev_queue = Queue() # event queue
terminate_event = Event()


def cadence_to_script():
    while not terminate_event.is_set():
        message = sys.stdin.readline()
        log.debug("inbound message: %s"%message)
        if message == "stop\n":
            log.info("stopping")
            terminate_event.set()
        else:
            log.info("Cadence says %s",message)
    log.info("Leaving control thread")

def script_to_cadence():
    while not terminate_event.is_set():
        try:
            message = out_queue.get(True,wait_secs)
            log.debug("sending: %s"%message)
            sys.stdout.write("%s\n"%message)
            sys.stdout.flush()
        except Empty:
            pass

    log.info("Leaving messaging thread")

button_state = dict()
joystick_state = dict()
joystick_threads = dict()

def joy_lin_repeat(number,mintime, maxtime):
    log.info("new thread %d, time: %f, max: %f"%(number,mintime,maxtime))
    try:
        while not terminate_event.is_set():
            val = joystick_state[number]
            if val == 0:
                break

            absval = val
            if val < 0:
                absval = -val

            ratio = (32767.0-absval)/32767.0 # 0 -> fast 1 -> slow
            delay = mintime + (maxtime - mintime) * ratio

            out_queue.put("JoystickValue(%d %d)"%(number,val))
            log.info("%d %d sleeping delay: %.4f"%(val,absval,delay))
            time.sleep(delay)
    except:
        pass

import select
def js_reader(config):
    try:
        with open(infile_path,"rb") as js_file:
            while not terminate_event.is_set():
                # Read one event
                while not terminate_event.is_set():
                    r,w,e = select.select([js_file],[], [], wait_secs)
                    if js_file in r:
                        event = js_file.read(EVENT_SIZE)
                        break
                if terminate_event.is_set():
                    break

                # decode it
                (tv_msec, value, type, number) = struct.unpack("IhBB", event)
                if (type == 1):
                    # button
                    button_state[number] = value
                    out_queue.put("ButtonChange(%d %d)"%(number,value))
                elif (type == 2):
                    joystick_state[number] = value
                    out_queue.put("JoystickChange(%d %d)"%(number,value))
                    if value != 0:
                        try:
                            axis_config = config["axes"][number]
                            if axis_config[0] == "lin_repeat":
                                min_time=axis_config[1]
                                max_time=axis_config[2]
                                joystick_threads[number] = Thread(target=joy_lin_repeat, args=(number,min_time,max_time))
                                joystick_threads[number].start()
                        except:
                            log.exception("bleh")
                            pass
                elif (type >128):
                    # Initial values
                    type -= 128
                    if (type == 1):
                        button_state[number] = value
                        log.info("New Button %d"%number)
                    elif type == 2:
                        joystick_state[number] = value
                        log.info("New Axis %d"%number)

                else:
                    out_queue.put("EventError(\"Unknown event type %d\")"%type)

    except:
        log.exception("Js_reader thread:")
        terminate_event.set()

    log.info("Leaving event loop")

def send_state():
    bstate = " ".join([ "%d"%button_state[x] for x in sorted(button_state.keys())])
    jstate = " ".join([ "%d"%joystick_state[x] for x in sorted(joystick_state.keys())])
    sys.stdout.write("CurrentState(\"%s\" \"%s\")\n" % (bstate,jstate))


def main():
    config = {
            "axes": {
                0: ("lin_repeat", 0.1, 0.5),
                1: ("lin_repeat", 0.1, 0.5),
                2: ("norepeat"),
            }
    }
    ev_thread = Thread(target=js_reader, name="js_reader", args = (config,))
    out_thread = Thread(target=script_to_cadence, name="to_cadence")
    in_thread = Thread(target=cadence_to_script, name="from_cadence")
    ev_thread.start()
    out_thread.start()
    in_thread.start()
    terminate_event.wait()
    log.info("leaving main thread")

if __name__ == '__main__':
    main()
