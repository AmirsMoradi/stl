import vtk


class VTKRenderer:
    def __init__(self, render_window):
        self.renderer = vtk.vtkRenderer()
        render_window.AddRenderer(self.renderer)

        self.actor = None
        self._setup_scene()

    def _setup_scene(self):
        self.renderer.SetBackground(0.90, 0.90, 0.92)

        self.renderer.LightFollowCameraOn()

    def load_stl(self, path):
        reader = vtk.vtkSTLReader()
        reader.SetFileName(path)
        reader.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        mapper.ScalarVisibilityOff()

        if self.actor:
            self.renderer.RemoveActor(self.actor)

        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().SetColor(0.7, 0.7, 0.7)

        self.renderer.AddActor(self.actor)
        self.renderer.ResetCamera()

    def set_wireframe(self, enabled: bool):
        if not self.actor:
            return
        prop = self.actor.GetProperty()
        if enabled:
            prop.SetRepresentationToWireframe()
        else:
            prop.SetRepresentationToSurface()

    def set_model_color(self, r, g, b):
        if self.actor:
            self.actor.GetProperty().SetColor(r, g, b)
