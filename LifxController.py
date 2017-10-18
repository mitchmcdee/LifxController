from lifxlan import *
import rumps
from PIL import Image

rumps.debug_mode(True)


# LIFX Controller class
class LifxController(rumps.App):
    # Initialise the class
    def __init__(self):
        super(LifxController, self).__init__('LifxController', None, 'icon.png', True)
        self.reset()

    def reset(self):
        # Clear menu, lights and groups
        self.menu.clear()
        self.lights = {} # Dictionary mapping LIFX light names to their LIFX objects
        self.groups = {} # Dictionary mapping group names to the names of the lights in them

        # Add initial menu items to the menu
        resetMenuItem = rumps.MenuItem('Hard Reset', callback=self.onReset)
        self.menu.update(['Groups', None, 'Individual', None, resetMenuItem, None])

    # Will attempt to refresh the active lights
    def onReset(self, sender):
        # Reset menu and restart light search
        self.reset()
        self.menu.add(self.quit_button)
        self.updateActiveLights()

    # Will run when a power button has been clicked
    def onPowerUpdate(self, sender):
        # Get the associated LIFX object or group
        light = self.lights.get(sender.name)
        group = self.groups.get(sender.name)

        # If no light or group was found, soft fail
        if light is None and group is None:
            return

        # Update state and label, toggle power
        sender.state = not sender.state
        sender.title = 'Power is ON' if sender.state else 'Power is OFF'

        # Update power for all lights in a group, or just the individual light
        try:
            if group:
                [self.lights[name].set_power(sender.state, 0, True) for name in group]
            else:
                light.set_power(sender.state, 0, True)

        # A light did not respond
        except WorkflowException:
            return

    # Will run when a slider has been updated
    def onSliderUpdate(self, sender):
        # Get the associated menu, LIFX object and group (if applicable)
        menu = self.menu.get(sender.name)
        light = self.lights.get(sender.name)
        group = self.groups.get(sender.name)

        # If no menu item or group or light was found, soft fail
        if menu is None or (light is None and group is None):
            return

        # Get all menu items
        items = dict(menu.items())

        # Get all the current HSBK slider values
        h = items['h_' + sender.name].value
        s = items['s_' + sender.name].value
        b = items['b_' + sender.name].value
        k = items['k_' + sender.name].value

        # Update values for all lights in a group, or just the individual light
        try:
            if group:
                [self.lights[name].set_color([h, s, b, k], 0, True) for name in group]
            else:
                light.set_color([h, s, b, k], 0, True)  

                # Get and set infrared value if supported
                if light.get_infrared():
                    i = items['i_' + sender.name].value
                    light.set_infrared(i)

        # A light did not respond
        except WorkflowException:
            return

    # Add new group light as a submenu with it's own controllable buttons/sliders
    def addGroup(self, name):
        # Get the associated group
        group = self.groups[name]

        # If no group was found, soft fail
        if group is None:
            return

        # Get initial light values
        # Note: HSBK values are retrieved from first light in group as an estimate
        try:
            h, s, b, k = self.lights[group[0]].get_color()
            powers = [self.lights[l].get_power() for l in group]
            p = 'ON' if 65535 in powers else 'OFF'

        # Light did not respond
        except WorkflowException:
            return

        # Create power button and colour sliders
        powerButton = rumps.MenuItem('Power is ' + p, name=name, callback=self.onPowerUpdate)
        powerButton.state = p == 'ON'
        hueSlider = rumps.SliderMenuItem('h_' + name, 0, h, 65535, self.onSliderUpdate, name)
        saturationSlider = rumps.SliderMenuItem('s_' + name, s, 0, 65535, self.onSliderUpdate, name)
        brightnessSlider = rumps.SliderMenuItem('b_' + name, b, 0, 65535, self.onSliderUpdate, name)
        kelvinSlider = rumps.SliderMenuItem('k_' + name, k, 2500, 9000, self.onSliderUpdate, name)

        # Create light menu and first element (necessary to create submenu)
        groupMenu = rumps.MenuItem(name)
        groupMenu.add(powerButton)

        # Add rest of submenu elements
        groupMenu.update([None, 'Hue', hueSlider, 'Saturation', saturationSlider,
                          'Brightness', brightnessSlider, 'Kelvin', kelvinSlider])

        # Add light submenu to the individual light list menu
        self.menu.insert_after('Groups', groupMenu)

    # Add new individual light as a submenu with it's own controllable buttons/sliders
    def addIndividual(self, name):
        # Get the associated LIFX object
        light = self.lights.get(name)

        # If no light was found, soft fail
        if light is None:
            return

        # Get initial light values
        try:
            h, s, b, k = light.get_color()
            i = light.get_infrared()
            p = 'ON' if light.get_power() else 'OFF'

        # Light did not respond
        except WorkflowException:
            return

        # Create power button and colour sliders
        powerButton = rumps.MenuItem('Power is ' + p, name=name, callback=self.onPowerUpdate)
        powerButton.state = p == 'ON'
        hueSlider = rumps.SliderMenuItem('h_' + name, h, 0, 65535, self.onSliderUpdate, name)
        saturationSlider = rumps.SliderMenuItem('s_' + name, s, 0, 65535, self.onSliderUpdate, name)
        brightnessSlider = rumps.SliderMenuItem('b_' + name, b, 0, 65535, self.onSliderUpdate, name)
        kelvinSlider = rumps.SliderMenuItem('k_' + name, k, 2500, 9000, self.onSliderUpdate, name)

        # Create light menu and first element (necessary to create submenu)
        lightMenu = rumps.MenuItem(name)
        lightMenu.add(powerButton)

        # Add rest of submenu elements
        lightMenu.update([None, 'Hue', hueSlider, 'Saturation', saturationSlider,
                          'Brightness', brightnessSlider, 'Kelvin', kelvinSlider])

        # Create and add infrared slider if supported
        if i:
            infraredSlider = rumps.SliderMenuItem('i_' + name, i, 0, 65535, self.onSliderUpdate, name)
            lightMenu.update(['Infrared', infraredSlider])

        # Add light submenu to the individual light list menu
        self.menu.insert_after('Individual', lightMenu)

    # Update the state a LIFX light
    def updateLightState(self, name):
        # Get the associated menu and LIFX object
        menu = self.menu.get(name)
        light = self.lights.get(name)

        # If no menu or light was found, soft fail
        if menu is None or light is None:
            return

        # Get updated light values
        try:
            h, s, b, k = light.get_color()
            i = light.get_infrared()
            p = 'ON' if light.get_power() else 'OFF'
            groupName = light.get_group()

        # Light did not respond
        except WorkflowException:
            return

        # Get all menu items
        items = dict(menu.items())

        # Update values
        powerMenuItem = items.get('Power is ON') if 'Power is ON' in items else items.get('Power is OFF')
        powerMenuItem.state = p == 'ON'
        powerMenuItem.title = 'Power is ' + p
        items['h_' + name].value = h
        items['s_' + name].value = s
        items['b_' + name].value = b
        items['k_' + name].value = k

        # Update infrared value if supported
        if i:
            items['i_' + sender.name].value = i

        # Update this light's group if it has one
        if groupName in self.groups:
            self.updateGroupState(groupName, [h, s, b, k])

    # Update the state of a group
    def updateGroupState(self, name, colourValues):
        # Get the associated group and menu
        group = self.groups.get(name)
        menu = self.menu.get(name)

        # If no group or menu was found, soft fail
        if group is None or menu is None:
            return

        # Get group power values
        try:
            powers = [self.lights[l].get_power() for l in group]
            p = 'ON' if 65535 in powers else 'OFF'

        # A light did not respond
        except WorkflowException:
            return

        # Get all group menu items
        items = dict(menu.items())

        # Update group values
        h, s, b, k = colourValues
        powerMenuItem = items.get('Power is ON') if 'Power is ON' in items else items.get('Power is OFF')
        powerMenuItem.state = p == 'ON'
        powerMenuItem.title = 'Power is ' + p
        items['h_' + name].value = h
        items['s_' + name].value = s
        items['b_' + name].value = b
        items['k_' + name].value = k

    # Removes the menu item from the menu as well as any dictionaries it is in
    def removeMenuItem(self, menuItem):
        if menuItem in self.menu:
            del self.menu[menuItem]
        if menuItem in self.lights:
            del self.lights[menuItem]
        if menuItem in self.groups:
            del self.groups[menuItem]

    # Timer event that keeps the list of active lights up to date
    @rumps.timer(10)
    def updateActiveLights(self, _):
        # Discovers all active LIFX lights on the network
        lights = LifxLAN().get_lights()

        # Loop through the discovered lights
        for light in lights:
            # Get light name and group if it has one
            try:
                name = light.get_label()
                group = light.get_group()

            # Light did not respond
            except WorkflowException:
                continue

            # If the light is a new light, add it to the dictionary of lights
            if name not in self.lights:
                self.lights[name] = light

            # If the light has no group, continue onto next light
            if group is None:
                continue

            # If the light has a group that's not in the dictionary of groups, add the new group
            if group not in self.groups:
                self.groups[group] = [name]

            # If the light is a part of a group, add it to that group if it hasn't been already
            if name not in self.groups[group]:
                self.groups[group].append(name)

        # Get active lights and groups
        try:
            activeLights = [l.get_label() for l in lights]
            activeGroups = [l.get_group() for l in lights]

        # A light did not respond
        except WorkflowException:
            return

        # Remove any inactive lights and groups from the menu
        for menuItem in list(self.menu.keys()):
            if menuItem not in self.lights and menuItem not in self.groups:
                continue
            if menuItem in activeLights or menuItem in activeGroups:
                continue
            self.removeMenuItem(menuItem)

    # Timer event that updates the menu with the active light's and their states
    @rumps.timer(2)
    def updateAllStates(self, _):
        # Update all updated light states
        [self.updateLightState(l) for l in list(self.lights.keys())]

        # Filter out any new lights or groups that aren't in the menu yet
        newLights = [l for l in self.lights if l not in list(self.menu.keys())]
        newGroups = [g for g in self.groups if g not in list(self.menu.keys())]

        # Add any new lights and groups to the menu
        [self.addIndividual(l) for l in newLights]
        [self.addGroup(g) for g in newGroups]


if __name__ == '__main__':
    # Create LifxController menu and run it
    LifxController().run()
