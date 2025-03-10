from panda3d.core import AmbientLight, DirectionalLight

class Light():
    def __init__(self): # Directional light (like the sun)
        dlight = DirectionalLight("dlight")
        dlight.setColor((1, 1, 1, 1))  # White light
        dlight_np = self.render.attachNewNode(dlight)
        dlight_np.setHpr(45, -60, 0)  # Angle the light downwards
        dlight_np.setPos(10, -10, 10)  # Position the light above the scene
        self.render.setLight(dlight_np)

            # Ambient light (fills in shadows)
        alight = AmbientLight("alight")
        alight.setColor((0.3, 0.3, 0.3, 1))  # Soft gray ambient light
        alight_np = self.render.attachNewNode(alight)
        self.render.setLight(alight_np)

            # Enable per-pixel lighting
        self.render.setShaderAuto()