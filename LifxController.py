import rumps
import lazylights as lazy
import re

# Discovers all the LIFX lights
bulbs = lazy.find_bulbs()

# Create a dictionary of bulb names to their state
namedBulbs = {s.label.strip(" \x00"): s for s in lazy.get_state(bulbs)}

class LifxController(rumps.App):
    # Loop through all accessible bulbs.
    for bulb in namedBulbs:
        # Get the initial state of the bulb (on or off).
        initialState = 'ON' if namedBulbs[bulb].power else 'OFF'

        # Add bulb as a menu item and toggle its power when clicked.
        @rumps.clicked('{0} is {1}'.format(bulb, initialState))
        def toggle_power(self, sender):
            # Get identifying label
            bulbLabel = re.search('(.*) is', sender.title).group(1)

            # Get bulb state
            bulbState = 1 if re.search('ON', sender.title) else 0

            # Toggle bulb power
            bulb = namedBulbs[bulbLabel].bulb
            lazy.set_power([bulb], not bulbState)

            # Update text in the menu item title
            oldState = 'ON' if bulbState else 'OFF'
            updatedState = 'OFF' if bulbState else 'ON'
            sender.title = sender.title.replace(oldState, updatedState)

if __name__ == '__main__':
    LifxController('LIFX Controller').run()