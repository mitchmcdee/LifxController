from lifxlan import *
import rumps

rumps.debug_mode(True)

# LIFX Controller class
class LifxController(rumps.App):

    # Initialise the class
    def __init__(self):
        super(LifxController, self).__init__('LifxController', None, 'icon.png', True)

        # Dictionary holding LIFX light names and their LIFX objects
        self.lights = {}

        # Create separator for individual lights and the Quit button
        self.menu.add(None)

    # Will run when a power button has been clicked
    def onPowerUpdate(self, sender):
        # Get the associated LIFX object
        light = self.lights[sender.name]

        # No light was found, soft fail
        if light is None:
            return

        # Update state and label, toggle power
        sender.state = not sender.state
        sender.title = 'Power is ON' if sender.state else 'Power is OFF'
        light.set_power(sender.state, 0, True)

    # Will run when a slider has been updated
    def onSliderUpdate(self, sender):
        # Get the associated menu and LIFX object
        menu = self.menu.get(sender.name)
        light = self.lights[sender.name]

        # No menu item or light was found, soft fail
        if menu is None or light is None:
            return

        # Get all menu items
        items = menu.items()

        # Get all the current HSBK slider values
        h = items[3][1].value
        s = items[5][1].value
        b = items[7][1].value
        k = items[9][1].value

        # Update colour
        light.set_color([h,s,b,k], 0, True)

    # Add new individual light as a submenu with it's own controllable buttons/sliders
    def addIndividualLight(self, name):
        # Get the associated LIFX object
        light = self.lights[name]

        # No light was found, soft fail
        if light is None:
            return

        # Get initial HSBK (hue, saturation, brightness, kelvin) and power values
        h,s,b,k = light.get_color()
        power = 'ON' if light.get_power() else 'OFF'

        # Create power button and colour sliders
        powerButton = rumps.MenuItem('Power is ' + power, name=name, callback=self.onPowerUpdate)
        hueSlider = rumps.SliderMenuItem('h_' + name, h, 0, 65535, self.onSliderUpdate, name)
        saturationSlider = rumps.SliderMenuItem('s_' + name, s, 0, 65535, self.onSliderUpdate, name)
        brightnessSlider = rumps.SliderMenuItem('b_' + name, b, 0, 65535, self.onSliderUpdate, name)
        kelvinSlider = rumps.SliderMenuItem('k_' + name, k, 2500, 9000, self.onSliderUpdate, name)

        # Create light menu and first element (necessary to create submenu)
        lightMenu = rumps.MenuItem(name)
        lightMenu.add(powerButton)

        # Add rest of submenu elements
        lightMenu.update([None, 'Hue', hueSlider, 'Saturation', saturationSlider,
                          'Brightness', brightnessSlider, 'Kelvin', kelvinSlider ])

        # Add light submenu to the individual light list menu (above seperator_1)
        self.menu.insert_before('separator_1', lightMenu)

    def updateState(self, name):
        # Get the associated menu and LIFX object
        menu = self.menu.get(name)
        light = self.lights[name]

        # No menu or light was found, soft fail
        if menu is None or light is None:
            return

        # Get updated HSBK and power values
        hue, saturation, brightness, kelvin = light.get_color()
        power = 'ON' if light.get_power() else 'OFF'

        # Update values
        menu.items()[0][1].state = power == 'ON'
        menu.items()[0][1].title = 'Power is ' + power
        menu.items()[3][1].value = hue
        menu.items()[5][1].value = saturation
        menu.items()[7][1].value = brightness
        menu.items()[9][1].value = kelvin
        
    # Timer event that keeps the list of active lights up to date
    @rumps.timer(10)
    def updateActiveLights(self, _):
        self.lights = {light.get_label(): light for light in LifxLAN().get_lights()}

    # Timer event that updates the menu with the active light's and their states
    @rumps.timer(5)
    def updateAllStates(self, _):
        # Filter any new lights
        newLights = filter(lambda light: light not in self.menu, self.lights)

        # Add any new lights to the menu
        map(self.addIndividualLight, newLights)

        # Update all updated light states
        map(self.updateState, self.lights)

if __name__ == '__main__':
    # Create LifxController menu and run it
    LifxController().run()
