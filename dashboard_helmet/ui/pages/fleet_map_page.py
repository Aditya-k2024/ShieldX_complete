from PySide6.QtWidgets import QWidget, QVBoxLayout
from ui.components.maps import MapWidget

class FleetMapPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.map_widget = MapWidget(is_fleet_map=True)
        layout.addWidget(self.map_widget)

    def update_map(self, helmet_data):
        self.map_widget.update_all_markers(helmet_data)