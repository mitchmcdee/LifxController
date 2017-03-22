from lifxlan import *
import rumps
import threading
rumps.debug_mode(True)

# Globally accessible dictionary holding LIFX light names and their LIFX objects
lights = {}

# LIFX Controller class
class LifxController(rumps.App):

    # Toggle light power when clicked
    def togglePower(self, sender):
        # Get the associated light for the menu item
        light = lights[sender.title]

        # No light was found, soft fail
        if light is None:
            return

        # Toggle state and power
        sender.state = not sender.state
        light.set_power(sender.state)

    def hi(self, value):
        lights['McDee\'s Bedroom'].set_brightness(value)

    def onSliderUpdate(self, sender):
        thread = threading.Thread(target=self.hi, args=(sender.value(), ))
        thread.daemon = True                            # Daemonize thread
        thread.start()
        

    # Add light as a clickable menu item
    def addLightToMenu(self, name):
        menuItem = rumps.MenuItem(name, callback=self.togglePower)
        menuItem.state = 0 # default light to display as off until updated
        slider = rumps.SliderMenuItem('Testing', callback=self.onSliderUpdate)
        self.menu.insert_before('Quit', menuItem)
        self.menu.insert_before('Quit', slider)

    # Updates the on/off state for a single LIFX light
    def updateState(self, name, light):
        # Get the associated menu item for the light
        menuItem = self.menu.get(name)

        # No menu item was found, soft fail
        if menuItem is None:
            return

        # Update the light's menu item state (light is on if power > 0)
        menuItem.state = light.get_power() > 0

    # Timer event that keeps the list of active lights up to date
    @rumps.timer(20)
    def updateActiveLights(self, _):
        global lights
        lights = {light.get_label(): light for light in LifxLAN().get_lights()}

    # Timer event that updates the menu with the active light's and their states
    @rumps.timer(20)
    def updateAllStates(self, _):
        # Loops through the active lights and updates their on off state. Also
        # will add newly discovered lights to the menu
        # TODO(mitch): redesign to use sub menus? icons? http://bit.ly/2nKCbNR
        for name, light in lights.iteritems():
            if name not in self.menu:
                self.addLightToMenu(name)
            self.updateState(name, light)

if __name__ == '__main__':
    # Create LifxController menu and run it
    LifxController('LifxController', None, 'icon.png', True).run()
