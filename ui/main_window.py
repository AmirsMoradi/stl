from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QToolBar,
    QColorDialog,
    QSlider,
    QLabel,
    QDialog,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QHBoxLayout
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from core.renderer import VTKRenderer
from core.measure import DistanceMeasure
from core.section import SectionPlane


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("STL Viewer – Qt + VTK")
        self.resize(1200, 800)

        self.vtk_widget = QVTKRenderWindowInteractor(self)
        self.setCentralWidget(self.vtk_widget)

        self.renderer = VTKRenderer(self.vtk_widget.GetRenderWindow())
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()

        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)
        self.interactor.Initialize()

        self.measure_enabled = False
        self.measure_tool = DistanceMeasure(
            self.renderer.renderer,
            get_model_bounds_callable=lambda: self.renderer.actor.GetBounds() if self.renderer.actor else None
        )
        self.section_tool = None
        self.section_active = False

        self.mode_label = QLabel("Mode: Orbit")
        self.statusBar().addPermanentWidget(self.mode_label)

        self._create_toolbar()

        self.interactor.AddObserver("LeftButtonPressEvent", self._on_left_button_press, 1.0)

    def _create_toolbar(self):
        tb = QToolBar("Main")
        self.addToolBar(tb)

        open_action = QAction("Open STL", self)
        open_action.triggered.connect(self.open_file)
        tb.addAction(open_action)

        wire_action = QAction("Wireframe", self)
        wire_action.setCheckable(True)
        wire_action.toggled.connect(self._on_wireframe_toggled)
        tb.addAction(wire_action)

        color_action = QAction("Color", self)
        color_action.triggered.connect(self.pick_color)
        tb.addAction(color_action)

        tb.addSeparator()

        measure_action = QAction("Measure", self)
        measure_action.setCheckable(True)
        measure_action.toggled.connect(self.toggle_measure)
        tb.addAction(measure_action)

        clear_measure_action = QAction("Clear Measure", self)
        clear_measure_action.triggered.connect(self.clear_measurements)
        tb.addAction(clear_measure_action)

        tb.addSeparator()

        self.section_slider = QSlider(Qt.Horizontal)
        self.section_slider.setRange(-100, 100)
        self.section_slider.setValue(0)
        self.section_slider.valueChanged.connect(self.update_section)
        tb.addWidget(self.section_slider)

        tb.addSeparator()

        help_action = QAction("Help", self)
        help_action.triggered.connect(self.show_help_dialog)
        tb.addAction(help_action)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open STL",
            "",
            "STL Files (*.stl)"
        )
        if not path:
            return

        self.renderer.load_stl(path)

        self.section_tool = SectionPlane(self.renderer.actor)
        self.section_tool.enable(False)
        self.section_active = False

        self.section_slider.setValue(0)

        self.vtk_widget.GetRenderWindow().Render()

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.renderer.set_model_color(
                color.redF(),
                color.greenF(),
                color.blueF()
            )
            self.vtk_widget.GetRenderWindow().Render()

    def _on_wireframe_toggled(self, enabled: bool):
        self.renderer.set_wireframe(enabled)
        self.vtk_widget.GetRenderWindow().Render()

    def toggle_measure(self, state: bool):
        self.measure_enabled = state
        if state:
            self.mode_label.setText("Mode: Measure")
        else:
            self.mode_label.setText("Mode: Orbit")

    def clear_measurements(self):
        self.measure_tool.clear()
        self.vtk_widget.GetRenderWindow().Render()

    def _on_left_button_press(self, obj, evt):
        if not self.measure_enabled:
            return

        if not self.renderer.actor:
            return

        x, y = self.interactor.GetEventPosition()

        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.0005)
        picked = picker.Pick(x, y, 0, self.renderer.renderer)

        if picked:
            pos = picker.GetPickPosition()
            self.measure_tool.add_point(pos)
            self.vtk_widget.GetRenderWindow().Render()

    def update_section(self, value):
        if not self.section_tool or not self.renderer.actor:
            return

        if not self.section_active:
            self.section_tool.enable(True)
            self.section_active = True

        self.section_tool.set_position(value)
        self.vtk_widget.GetRenderWindow().Render()

    def show_help_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("راهنمای برنامه | STL Viewer Help")
        dialog.resize(760, 560)

        layout = QVBoxLayout(dialog)

        text = QTextEdit(dialog)
        text.setReadOnly(True)
        text.setAcceptRichText(True)
        text.setLineWrapMode(QTextEdit.WidgetWidth)

        text.setStyleSheet("""
            QTextEdit {
                background: #f7f9fc;
                color: #1f2937;
                border: 1px solid #d0d7e2;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-family: "Segoe UI", "Vazirmatn", "Tahoma";
            }
        """)

        help_html = """
        <h2 style="margin-bottom:4px;">راهنمای استفاده از STL Viewer</h2>
        <p style="color:#4b5563;margin-top:0;">
            نسخه Qt + VTK — راهنمای سریع و کاربردی
        </p>

        <hr>

        <h3>1) باز کردن فایل STL</h3>
        <ul>
          <li>از دکمه <b>Open STL</b> استفاده کنید.</li>
          <li>فایل با پسوند <code>.stl</code> را انتخاب کنید.</li>
        </ul>

        <h3>2) کنترل نمایش مدل</h3>
        <ul>
          <li><b>کلیک چپ + حرکت:</b> چرخش مدل (Orbit)</li>
          <li><b>کلیک وسط</b> یا <b>Shift + کلیک چپ + حرکت:</b> جابجایی (Pan)</li>
          <li><b>اسکرول ماوس:</b> بزرگ‌نمایی / کوچک‌نمایی (Zoom)</li>
        </ul>

        <h3>3) نمایش سیمی (Wireframe)</h3>
        <ul>
          <li>با فعال‌کردن <b>Wireframe</b>، مدل به‌صورت شبکه‌ای نمایش داده می‌شود.</li>
        </ul>

        <h3>4) تغییر رنگ مدل</h3>
        <ul>
          <li>روی <b>Color</b> کلیک کنید و رنگ دلخواه را انتخاب نمایید.</li>
        </ul>

        <h3>5) اندازه‌گیری فاصله (Measure)</h3>
        <ul>
          <li>دکمه <b>Measure</b> را فعال کنید.</li>
          <li>روی نقطه اول مدل کلیک کنید (P1).</li>
          <li>روی نقطه دوم کلیک کنید (P2).</li>
          <li>فاصله بین دو نقطه نمایش داده می‌شود.</li>
          <li>برای پاک‌کردن نتایج، از <b>Clear Measure</b> استفاده کنید.</li>
        </ul>

        <h3>6) برش مقطعی (Section)</h3>
        <ul>
          <li>با اسلایدر بخش <b>Section</b> موقعیت صفحه برش را تغییر دهید.</li>
          <li>برای بازگشت به حالت میانی، اسلایدر را روی <b>0</b> قرار دهید.</li>
        </ul>

        <h3>نکات مهم</h3>
        <ul>
          <li>قبل از Measure حتماً فایل STL را باز کنید.</li>
          <li>اگر چرخش غیرعادی شد، Measure را خاموش کنید و دوباره تست بگیرید.</li>
          <li>برای دید بهتر، رنگ مدل و حالت Wireframe را متناسب تنظیم کنید.</li>
          <li>وقتی اندازه دونقطه را در پایان تصویر مشاهده کردید واحد model unit میباشد . model unit = mm </li>
        </ul>

        <hr>
        <p style="color:#6b7280;">
          این راهنما داخل برنامه قابل دسترسی است و برای کاربران نهایی طراحی شده است.
        </p>
        """

        text.setHtml(help_html)
        layout.addWidget(text)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("بستن")
        close_btn.setMinimumWidth(110)
        close_btn.clicked.connect(dialog.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 12px;
                font-family: "Segoe UI", "Vazirmatn", "Tahoma";
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            QPushButton:pressed {
                background: #1e40af;
            }
        """)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        dialog.exec()
