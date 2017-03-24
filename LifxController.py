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
        print(sender.name)

        # Get the associated menu and LIFX object
        menu = self.menu.get(sender.name)
        light = self.lights[sender.name]

        # No menu item or light was found, soft fail
        if menu is None or light is None:
            return

        # Get all menu items
        items = menu.items()

        # Get all the current HSBK slider values
        hue = items[3][1].value
        saturation = items[5][1].value
        brightness = items[7][1].value
        kelvin = items[9][1].value

        # Update colour
        light.set_color([hue, saturation, brightness, kelvin], 0, True)

    # Add light as a submenu with it's own controllable buttons/sliders
    def addLightToMenu(self, name):
        light = self.lights[name]

        # No light was found, soft fail
        if light is None:
            return

        # Get initial HSBK and power values
        hue, saturation, brightness, kelvin = light.get_color()
        power = 'ON' if light.get_power() else 'OFF'

        # Create power button and colour sliders
        powerButton = rumps.MenuItem('Power is ' + power, name=name, callback=self.onPowerUpdate)
        brightnessSlider = rumps.SliderMenuItem('b_' + name, brightness, 0, 65535, self.onSliderUpdate, name)
        hueSlider = rumps.SliderMenuItem('h_' + name, hue, 0, 65535, self.onSliderUpdate, name)
        saturationSlider = rumps.SliderMenuItem('s_' + name, saturation, 0, 65535, self.onSliderUpdate, name)
        kelvinSlider = rumps.SliderMenuItem('k_' + name, kelvin, 2500, 9000, self.onSliderUpdate, name)

        self.menu.update({name: [
                            powerButton,
                            None,
                            'Hue', hueSlider,
                            'Saturation', saturationSlider,
                            'Brightness', brightnessSlider,
                            'Kelvin', kelvinSlider
                        ]})

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
        newLights = filter(lambda light: light not in self.menu, self.lights)
        map(self.addLightToMenu, newLights)
        map(self.updateState, self.lights)

if __name__ == '__main__':
    # Create LifxController menu and run it
    LifxController().run()
