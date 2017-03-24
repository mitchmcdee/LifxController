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

        # Dictionary holding group names and the names of the lights in them
        self.groups = {}

        # Create separators for individual lights, groups and the Quit button
        self.menu.update(['Groups', None, 'Individual', None])


    # Will run when a power button has been clicked
    def onPowerUpdate(self, sender):
        # Get the associated LIFX object or group
        light = self.lights.get(sender.name)
        group = self.groups.get(sender.name)

        # No lights or groups were found, soft fail
        if light is None and group is None:
            return

        # Update state and label, toggle power
        sender.state = not sender.state
        sender.title = 'Power is ON' if sender.state else 'Power is OFF'

        # Update power for all lights in a group, or just the individual light
        if group:
            [self.lights.get(name).set_power(sender.state, 0, True) for name in group]
        else:
            light.set_power(sender.state, 0, True)


    # Will run when a slider has been updated
    def onSliderUpdate(self, sender):
        # Get the associated menu, LIFX object and group (if applicable)
        menu = self.menu.get(sender.name)
        light = self.lights.get(sender.name)
        group = self.groups.get(sender.name)

        # No menu item was found or a group or light wasn't found, soft fail
        if menu is None or (light is None and group is None):
            return

        # Get all menu items
        items = menu.items()

        # Get all the current HSBK slider values
        h = items[3][1].value
        s = items[5][1].value
        b = items[7][1].value
        k = items[9][1].value

        # Update values for all lights in a group, or just the individual light
        if group:
            [self.lights.get(name).set_color([h,s,b,k], 0, True) for name in group]
        else:
            light.set_color([h,s,b,k], 0, True)


    # Add new group light as a submenu with it's own controllable buttons/sliders
    def addGroupLight(self, name):
        # Get the associated group
        group = self.groups.get(name)

        # No group was found, soft fail
        if group is None:
            return

        # Get initial HSBK (hue, saturation, brightness, kelvin) and power values
        # Note: HSBK values are retrieved from first light in group as an estimate
        h,s,b,k = self.lights.get(group[0]).get_color()
        powers = [self.lights.get(light).get_power() for light in group]
        power = 'ON' if 65535 in powers else 'OFF'

        # Create power button and colour sliders
        powerButton = rumps.MenuItem('Power is ' + power, name=name, callback=self.onPowerUpdate)
        powerButton.state = power == 'ON'
        hueSlider = rumps.SliderMenuItem('h_' + name, 0, h, 65535, self.onSliderUpdate, name)
        saturationSlider = rumps.SliderMenuItem('s_' + name, s, 0, 65535, self.onSliderUpdate, name)
        brightnessSlider = rumps.SliderMenuItem('b_' + name, b, 0, 65535, self.onSliderUpdate, name)
        kelvinSlider = rumps.SliderMenuItem('k_' + name, k, 2500, 9000, self.onSliderUpdate, name)

        # Create light menu and first element (necessary to create submenu)
        groupMenu = rumps.MenuItem(name)
        groupMenu.add(powerButton)

        # Add rest of submenu elements
        groupMenu.update([None, 'Hue', hueSlider, 'Saturation', saturationSlider,
                          'Brightness', brightnessSlider, 'Kelvin', kelvinSlider ])

        # Add light submenu to the individual light list menu (above seperator_1)
        self.menu.insert_before('separator_1', groupMenu)


    # Add new individual light as a submenu with it's own controllable buttons/sliders
    def addIndividualLight(self, name):
        # Get the associated LIFX object
        light = self.lights.get(name)

        # No light was found, soft fail
        if light is None:
            return

        # Get initial HSBK (hue, saturation, brightness, kelvin) and power values
        h,s,b,k = light.get_color()
        power = 'ON' if light.get_power() else 'OFF'

        # Create power button and colour sliders
        powerButton = rumps.MenuItem('Power is ' + power, name=name, callback=self.onPowerUpdate)
        powerButton.state = power == 'ON'
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

        # Add light submenu to the individual light list menu (above seperator_2)
        self.menu.insert_before('separator_2', lightMenu)


    # Update the state of a group
    def updateGroup(self, name):
        # Get the associated menu and group
        menu = self.menu.get(name)
        group = self.groups.get(name)

        # No menu or group was found, soft fail
        if menu is None or group is None:
            return

        # Note: We can't represent all light's updated HSBK values, but we can display
        # the group power state by checking to see if at least one group light is ON
        powers = [self.lights.get(light).get_power() for light in group]
        power = 'ON' if 65535 in powers else 'OFF'

        # Update values
        menu.items()[0][1].state = power == 'ON'
        menu.items()[0][1].title = 'Power is ' + power


    # Update the state a LIFX light
    def updateState(self, name):
        # Get the associated menu and LIFX object
        menu = self.menu.get(name)
        light = self.lights.get(name)

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

        if light.get_group() in self.groups:
            self.updateGroup(light.get_group())
        

    # Timer event that keeps the list of active lights up to date
    @rumps.timer(10)
    def updateActiveLights(self, _):
        # Loop through the discovered lights
        for light in LifxLAN().get_lights():
            # Get light name and group if it has one
            name = light.get_label()
            group = light.get_group()

            # If the light has a group that's not in the dictionary of groups, add the new group
            if group not in self.groups:
                self.groups[group] = [name]

            # If the light is a new light, add it to the dictionary of lights
            if name not in self.lights:
                self.lights[name] = light

                # If the light is a part of a group, add it to that group if it hasn't been already
                if group and name not in self.groups.get(group):
                    self.groups.get(group).append(name)


    # Timer event that updates the menu with the active light's and their states
    @rumps.timer(5)
    def updateAllStates(self, _):
        # Filter any new lights
        newLights = filter(lambda light: light not in self.menu, self.lights)
        newGroups = filter(lambda group: group not in self.menu, self.groups)

        # Add any new lights and groups to the menu
        map(self.addIndividualLight, newLights)
        map(self.addGroupLight, newGroups)

        # Update all updated light states
        map(self.updateState, self.lights)


if __name__ == '__main__':
    # Create LifxController menu and run it
    LifxController().run()
