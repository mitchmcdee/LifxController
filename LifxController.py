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
        # Clear menu
        self.menu.clear()

        # Dictionary holding LIFX light names and their LIFX objects
        self.lights = {}

        # Dictionary holding group names and the names of the lights in them
        self.groups = {}

        # Add initial menu items to the menu
        refreshMenuItem = rumps.MenuItem('Refresh', callback=self.onRefresh)
        self.menu.update(['Groups', None, 'Individual', None, refreshMenuItem])


    # Will attempt to refresh the active lights
    def onRefresh(self, sender):
        # Reset menu and re-add quit button
        self.reset()
        self.menu.add(self.quit_button)

        # Rediscover lights and add them back to menu
        self.updateActiveLights()

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
            [self.lights[name].set_power(sender.state, 0, True) for name in group]
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
        items = dict(menu.items())

        # Get all the current HSBK slider values
        h = items['h_' + sender.name].value
        s = items['s_' + sender.name].value
        b = items['b_' + sender.name].value
        k = items['k_' + sender.name].value

        # Update values for all lights in a group, or just the individual light
        if group:
            [self.lights[name].set_color([h, s, b, k], 0, True) for name in group]
        else:
            light.set_color([h, s, b, k], 0, True)

            # Get and set infrared value if supported
            if light.get_infrared():
                i = items['i_' + sender.name].value
                light.set_infrared(i)

    # Add new group light as a submenu with it's own controllable buttons/sliders
    def addGroup(self, name):
        # Get the associated group
        group = self.groups[name]

        # No group was found, soft fail
        if group is None:
            return

        # Get initial HSBK (hue, saturation, brightness, kelvin) and power values
        # Note: HSBK values are retrieved from first light in group as an estimate
        h, s, b, k = self.lights[group[0]].get_color()
        powers = [self.lights[l].get_power() for l in group]
        power = 'ON' if 65535 in powers else 'OFF'

        # Create power button and colour sliders
        powerButton = rumps.MenuItem('Power is ' + power, name=name, callback=self.onPowerUpdate)
        powerButton.state = power == 'ON'
        hueSlider = rumps.SliderMenuItem('h_' + name, 0, h, 65535, self.onSliderUpdate, name)
        saturationSlider = rumps.SliderMenuItem('s_' + name, s, 0, 65535, self.onSliderUpdate, name)
        brightnessSlider = rumps.SliderMenuItem('b_' + name, b, 0, 65535, self.onSliderUpdate, name)
        kelvinSlider = rumps.SliderMenuItem('k_' + name, k, 2500, 9000, self.onSliderUpdate, name)

        # Create light menu and first element (necessary to create submenu)
        groupMenu = rumps.MenuItem(name, icon=self.generateIcon(name, [h, s, b, k, power]))
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

        # No light was found, soft fail
        if light is None:
            return

        # Get initial HSBK (hue, saturation, brightness, kelvin) and power values
        h, s, b, k = light.get_color()
        power = 'ON' if light.get_power() else 'OFF'

        # Create power button and colour sliders
        powerButton = rumps.MenuItem('Power is ' + power, name=name, callback=self.onPowerUpdate)
        powerButton.state = power == 'ON'
        hueSlider = rumps.SliderMenuItem('h_' + name, h, 0, 65535, self.onSliderUpdate, name)
        saturationSlider = rumps.SliderMenuItem('s_' + name, s, 0, 65535, self.onSliderUpdate, name)
        brightnessSlider = rumps.SliderMenuItem('b_' + name, b, 0, 65535, self.onSliderUpdate, name)
        kelvinSlider = rumps.SliderMenuItem('k_' + name, k, 2500, 9000, self.onSliderUpdate, name)

        # Create light menu and first element (necessary to create submenu)
        lightMenu = rumps.MenuItem(name, icon=self.generateIcon(name, [h, s, b, k, power]))
        lightMenu.add(powerButton)

        # Add rest of submenu elements
        lightMenu.update([None, 'Hue', hueSlider, 'Saturation', saturationSlider,
                          'Brightness', brightnessSlider, 'Kelvin', kelvinSlider])

        # Create and add infrared slider if supported
        if light.get_infrared():
            i = light.get_infrared()
            infraredSlider = rumps.SliderMenuItem('i_' + name, i, 0, 65535, self.onSliderUpdate, name)
            lightMenu.update(['Infrared', infraredSlider])

        # Add light submenu to the individual light list menu
        self.menu.insert_after('Individual', lightMenu)

    # Update the state a LIFX light
    def updateIndividualState(self, name):
        # Get the associated menu and LIFX object
        menu = self.menu.get(name)
        light = self.lights.get(name)

        # No menu or light was found, soft fail
        if menu is None or light is None:
            return

        # Get updated HSBK and power values
        h, s, b, k = light.get_color()
        p = 'ON' if light.get_power() else 'OFF'

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
        if light.get_infrared():
            items['i_' + sender.name].value = light.get_infrared()

        # Update menu colour icon
        menu.set_icon(self.generateIcon(name, [h, s, b, k, p]))

        # Update this light's group if it has one
        groupName = light.get_group()
        if groupName in self.groups:
            self.updateGroupState(groupName, [h, s, b, k])

    # Update the state of a group
    def updateGroupState(self, name, colourValues):
        # Get the associated group and menu
        group = self.groups.get(name)
        menu = self.menu.get(name)

        # No group menu was found, soft fail
        if menu is None:
            return

        # Get all group menu items
        items = dict(menu.items())

        # Get group power values
        powers = [self.lights[l].get_power() for l in group]
        p = 'ON' if 65535 in powers else 'OFF'

        # Update group values
        h, s, b, k = colourValues
        powerMenuItem = items.get('Power is ON') if 'Power is ON' in items else items.get('Power is OFF')
        powerMenuItem.state = p == 'ON'
        powerMenuItem.title = 'Power is ' + p
        items['h_' + name].value = h
        items['s_' + name].value = s
        items['b_' + name].value = b
        items['k_' + name].value = k

        # Update menu colour icon
        menu.set_icon(self.generateIcon(name, [h, s, b, k, p]))

    # Returns a coloured LIFX bulb icon based off of the given colour values
    def generateIcon(self, name, colourValues):
        # Translates a range onto another range
        def translateRange(value, leftMin, leftMax, rightMin, rightMax):
            # Figure out how 'wide' each range is
            leftSpan = leftMax - leftMin
            rightSpan = rightMax - rightMin

            # Convert the left range into a 0-1 range ( float)
            valueScaled = float(value - leftMin) / float(leftSpan)

            # Convert the 0-1 range into a value in the right range.
            return rightMin + (valueScaled * rightSpan)

        # Converts HSV values to RGB
        def HSVtoRGB(h, s, v):
            if s == 0.0: return [v, v, v]
            i = int(h * 6.)  # XXX assume int() truncates!
            f = (h * 6.) - i
            p, q, t = v * (1. - s), v * (1. - s * f), v * (1. - s * (1. - f))
            i %= 6
            if i == 0: return [v, t, p]
            if i == 1: return [q, v, p]
            if i == 2: return [p, v, t]
            if i == 3: return [p, q, v]
            if i == 4: return [t, p, v]
            if i == 5: return [v, p, q]

        h, s, b, k, power = colourValues

        # Open template image
        icon = Image.open('menuIconTemplate.png')
        icon = icon.convert('RGBA')
        image = icon.getdata()

        # If powered on, set colours, else, set to black to show power off
        if power == 'ON':
            # Map to correct HSV ranges
            h = translateRange(h, 0, 65535, 0, 1)
            s = translateRange(s, 0, 65535, 0, 1)
            b = translateRange(b, 0, 65535, 0, 1)

            # Convert HSV to RGB
            colour = HSVtoRGB(h, s, b)

            # Map to correct RGB ranges
            r = int(translateRange(colour[0], 0, 1, 0, 255))
            g = int(translateRange(colour[1], 0, 1, 0, 255))
            b = int(translateRange(colour[2], 0, 1, 0, 255))

        else:
            r, g, b = 0, 0, 0

        # Create new image by replacing white pixels with the correct colour
        newImage = []
        for pixel in image:
            if pixel[0] == 255 and pixel[1] == 255 and pixel[2] == 255:
                newImage.append((r, g, b, 255))
            else:
                newImage.append(pixel)

        # Save image and return the result
        icon.putdata(newImage)
        icon.save(name + '.png', 'PNG')
        return name + '.png'

    # Timer event that keeps the list of active lights up to date
    @rumps.timer(10)
    def updateActiveLights(self, _):
        # Discovers all active LIFX lights on the network
        lights = LifxLAN().get_lights()

        # Loop through the discovered lights
        for light in lights:
            # Get light name and group if it has one
            name = light.get_label()
            group = light.get_group()

            # If the light has a group that's not in the dictionary of groups, add the new group
            if group is not None and group not in self.groups:
                self.groups[group] = [name]

            # If the light is a new light, add it to the dictionary of lights
            if name not in self.lights:
                self.lights[name] = light

                # If the light is a part of a group, add it to that group if it hasn't been already
                if group is not None and name not in self.groups[group]:
                    self.groups[group].append(name)

        # Remove any inactive lights and groups from the menu
        activeLights = [light.get_label() for light in lights]
        activeGroups = [light.get_group() for light in lights]
        for menuItem in self.menu:
            if menuItem not in self.lights and menuItem not in self.groups:
                continue
            if menuItem in activeLights or menuItem in activeGroups:
                continue
            self.removeMenuItem(menuItem)

    # Removes the menu item from the menu as well as any dictionaries it is in
    def removeMenuItem(self, menuItem):
        print('Removing', menuItem)
        del self.menu[menuItem]
        if menuItem in self.lights:
            del self.lights[menuItem]
        if menuItem in self.groups:
            del self.groups[menuItem]

    # Timer event that updates the menu with the active light's and their states
    @rumps.timer(2)
    def updateAllStates(self, _):
        # Filter out any new lights or groups that aren't in the menu yet
        newLights = [l for l in self.lights if l not in self.menu]
        newGroups = [g for g in self.groups if g not in self.menu]

        # Add any new lights and groups to the menu
        [self.addIndividual(l) for l in newLights]
        [self.addGroup(g) for g in newGroups]

        # Update all updated light states
        [self.updateIndividualState(l) for l in self.lights]


if __name__ == '__main__':
    # Create LifxController menu and run it
    LifxController().run()
