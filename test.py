import rumps
from lifxlan import *

lifx = LifxLAN()
devices = lifx.get_lights()

# Toggles the power of a bulb given a state.
def toggle_power(bulb, state):
    if state:
        bulb.set_power("on")
    else:
        bulb.set_power("off")

class LifxController(rumps.App):
    # Loop through devices to get all bulbs
    for i in range(0, len(devices)):

        # Adds each bulb as an individual menu item
        @rumps.clicked("LIFX Bulb {0}".format(i))
        def onoff(self, sender):
            # Flip clicked state (shown as tick on the menu item)
            sender.state = not sender.state

            # Get bulb number (checks final char in menu item title)
            # TODO(mitch): this won't support >9 bulbs
            bulbNumber = int(sender.title[-1])

            # Toggle the power to that bulb
            toggle_power(devices[bulbNumber], sender.state)

if __name__ == "__main__":
    LifxController("LIFX Controller").run()