from lifxlan import *
import rumps
import re

# Discovers all the LIFX lights and puts them in a dictionary with their labels.
lights = {light.get_label(): light for light in LifxLAN().get_lights()}

class LifxController(rumps.App):
    # Loop through all accessible lights.
    for name, light in lights.iteritems():
        # Get the initial state of the light (on or off).
        initialState = 'ON' if light.get_power() else 'OFF'

        # Add light as a menu item and toggle its power when clicked.
        @rumps.clicked('{0} is {1}'.format(name, initialState))
        def toggle_power(self, sender):
            # Get identifying label
            lightLabel = re.search('(.*) is O', sender.title).group(1)

            # Get light state
            lightState = 1 if re.search('ON', sender.title) else 0

            # Toggle light power
            lights[lightLabel].set_power(not lightState)

            # Update text in the menu item title
            oldState = 'ON' if lightState else 'OFF'
            updatedState = 'OFF' if lightState else 'ON'
            sender.title = sender.title.replace(oldState, updatedState)

if __name__ == '__main__':
    LifxController('LifxController', None, 'images/icon.png').run()