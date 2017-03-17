import rumps
from lifxlan import *

lifx = LifxLAN()
devices = lifx.get_lights()

class LifxController(rumps.App):
    for i in range(0, len(devices)):
        
        @rumps.clicked("LIFX Bulb {0}".format(i))
        def onoff(self, sender):
            sender.state = not sender.state

            bulbNumber = int(sender.title[-1])
            if sender.state:
                devices[bulbNumber].set_power("on")
            else:
                devices[bulbNumber].set_power("off")

if __name__ == "__main__":
    LifxController("LIFX Controller").run()