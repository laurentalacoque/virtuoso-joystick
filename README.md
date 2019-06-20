# virtuoso-joystick
A barebone skill/python bundle to provide joystick support to cadence virtuoso

**WARNING**
This is currently highly experimental

## Quick and dirty install

* cp both `src/*` files to the working directory
* launch cadence virtuoso
* in the CIW, execute `load("joystick.sk")`

## Adapt to your needs

### Joystick buttons

* the skill function `ButtonChange(button_number, button_value)` in `joystick.sk` gets called whenever a button state changes.
  Implement your code here.
  button_value can take the two values 0 (released) and 1 (pressed)

### Joystick movements (a.k.a. _axes_)

* Whenever the position of one of the joystick axes change, the function `JoystickChange(axis_number value)` in `joystick.sk` is    
  called. This is called only once at each joystick position change. Implement your code here.
  `value` is an integer between `-32767` (full movement in one direction) and `32767` (full movement in the other direction). 
  A value of `0` indicates the resting position
  
* You can configure each axis with a repeat mode. In repeat mode, whenever the joystick isn't in its resting position, the function
  `JoystickValue(axis_number value)` in `joystick.sk` is called repeatedly (with a higher frequency when you apply a stronger
  force). This is useful for, e.g. scrolling when you want the scrolling to get faster whenever you apply stronger pressure to the joystick. The `value` argument is the same as above.:w
  
Configuration of the axes behavior is done in `joystick_reader.py/main()` function. 

The following configuration declares axes 0 and 1 to be `lin_repeat` mode (i.e. with a linear progression of the delay between two `JoystickValue` events). The values 0.1 and 0.5 define the fast frequency (1/0.1 second) when the joystick position is at its max and the slow frequency (1/0.5 second) when the joystick position just leaves its resting position.

The third axis (axis 2) is in mode `no_repeat`: `JoystickValue` won't get called for it but `JoystickChange` will be called whenever the joystick position changes.

```python

    config = {
              "axes": {
                  0: ("lin_repeat", 0.1, 0.5),
                  1: ("lin_repeat", 0.1, 0.5),
                  2: ("norepeat"),
              }

```
