import vtk
import math


class DistanceMeasure:
    def __init__(self, renderer, get_model_bounds_callable=None):
        self.renderer = renderer
        self.points = []
        self.actors = []
        self.unit_label = "cm"
        self.unit_conversion_factor = 0.1
        self.get_model_bounds = get_model_bounds_callable

        self.point_colors = [(1.0, 0.2, 0.2), (0.2, 1.0, 0.2)]
        self.line_color = (1.0, 1.0, 0.0)
        self.label_color = (1.0, 1.0, 1.0)

    def set_unit_label(self, label: str):
        self.unit_label = label
        l = label.lower().strip()
        if l == "mm":
            self.unit_conversion_factor = 1.0
        elif l == "cm":
            self.unit_conversion_factor = 0.1
        elif l == "m":
            self.unit_conversion_factor = 0.001

    def add_point(self, position):
        idx = len(self.points)
        self.points.append(position)

        self._draw_marker(position, idx)
        self._draw_point_label(position, f"P{idx + 1}")

        if len(self.points) == 2:
            self._draw_line()
            self._draw_distance_text_2d()
            self.points.clear()

    def clear(self):
        for a in self.actors:
            if isinstance(a, vtk.vtkTextActor):
                self.renderer.RemoveActor2D(a)
            else:
                self.renderer.RemoveActor(a)
        self.actors.clear()
        self.points.clear()

    def _model_diagonal(self):
        try:
            if self.get_model_bounds is None:
                return 100.0
            b = self.get_model_bounds()
            if not b:
                return 100.0
            xmin, xmax, ymin, ymax, zmin, zmax = b
            dx = xmax - xmin
            dy = ymax - ymin
            dz = zmax - zmin
            d = math.sqrt(dx * dx + dy * dy + dz * dz)
            return d if d > 1e-9 else 100.0
        except Exception:
            return 100.0

    def _marker_radius(self):
        return max(0.1, self._model_diagonal() * 0.006)

    def _label_offset(self):
        return self._marker_radius() * 1.8

    def _draw_marker(self, pos, idx):
        sphere = vtk.vtkSphereSource()
        sphere.SetRadius(self._marker_radius())
        sphere.SetCenter(pos)
        sphere.SetThetaResolution(24)
        sphere.SetPhiResolution(24)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        color = self.point_colors[idx % len(self.point_colors)]
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetAmbient(0.35)
        actor.GetProperty().SetDiffuse(0.65)

        self.renderer.AddActor(actor)
        self.actors.append(actor)

    def _draw_point_label(self, pos, text_value):
        off = self._label_offset()
        lx, ly, lz = pos[0] + off, pos[1] + off, pos[2] + off

        lbl = vtk.vtkBillboardTextActor3D()
        lbl.SetInput(text_value)
        lbl.SetPosition(lx, ly, lz)
        lbl.GetTextProperty().SetFontSize(20)
        lbl.GetTextProperty().SetColor(*self.label_color)
        lbl.GetTextProperty().SetBold(True)
        lbl.GetTextProperty().SetShadow(True)

        self.renderer.AddActor(lbl)
        self.actors.append(lbl)

    def _draw_line(self):
        p1, p2 = self.points

        line = vtk.vtkLineSource()
        line.SetPoint1(p1)
        line.SetPoint2(p2)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(line.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*self.line_color)
        actor.GetProperty().SetLineWidth(3.0)

        self.renderer.AddActor(actor)
        self.actors.append(actor)

    def _draw_distance_text_2d(self):
        p1, p2 = self.points
        dist = math.dist(p1, p2)
        dist_converted = dist * self.unit_conversion_factor

        text = vtk.vtkTextActor()
        text.SetInput(f"Distance: {dist_converted:.3f} {self.unit_label}")
        text.SetPosition(20, 20)
        text.GetTextProperty().SetColor(1, 1, 1)
        text.GetTextProperty().SetFontSize(18)
        text.GetTextProperty().SetBold(True)

        self.renderer.AddActor2D(text)
        self.actors.append(text)
