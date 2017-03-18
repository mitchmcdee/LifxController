from lifxlan import *
import rumps
import re

# Discovers all the LIFX lights
bulbs = {bulb.get_label(): bulb for bulb in LifxLAN().get_lights()}

class LifxController(rumps.App):
    # Loop through all accessible bulbs.
    for name, bulb in bulbs.iteritems():
        # Get the initial state of the bulb (on or off).
        initialState = 'ON' if bulb.get_power() else 'OFF'

        # Add bulb as a menu item and toggle its power when clicked.
        @rumps.clicked('{0} is {1}'.format(name, initialState))
        def toggle_power(self, sender):
            # Get identifying label
            bulbLabel = re.search('(.*) is', sender.title).group(1)

            # Get bulb state
            bulbState = 1 if re.search('ON', sender.title) else 0

            # Toggle bulb power
            bulbs[bulbLabel].set_power(not bulbState)

            # Update text in the menu item title
            oldState = 'ON' if bulbState else 'OFF'
            updatedState = 'OFF' if bulbState else 'ON'
            sender.title = sender.title.replace(oldState, updatedState)

if __name__ == '__main__':
    LifxController('LifxController', None, 'icon.png').run()