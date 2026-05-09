import vtk


class SectionPlane:
    def __init__(self, actor):
        self.actor = actor

        self.plane = vtk.vtkPlane()
        self.plane.SetOrigin(0, 0, 0)
        self.plane.SetNormal(1, 0, 0)

        mapper = actor.GetMapper()
        mapper.RemoveAllClippingPlanes()
        mapper.AddClippingPlane(self.plane)

    def set_position(self, slider_value):

        if not self.actor:
            return

        bounds = self.actor.GetBounds()
        xmin, xmax = bounds[0], bounds[1]

        t = (slider_value + 100.0) / 200.0
        x = xmin + t * (xmax - xmin)

        self.plane.SetOrigin(x, 0, 0)

    def enable(self, state: bool):
        mapper = self.actor.GetMapper()
        if state:
            mapper.AddClippingPlane(self.plane)
        else:
            mapper.RemoveAllClippingPlanes()
