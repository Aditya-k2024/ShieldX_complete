from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QLabel, QFormLayout, 
    QGraphicsDropShadowEffect, QHBoxLayout 
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# --- IMPORTS ---
from ui.components.shared import AnimatedLabel
from ui.components.cards import BatteryCard, LiveAlertPanel
from ui.components.graphs import FocusGraphCanvas
from ui.components.maps import MapWidget

class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_layout = QGridLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(15)
        
        # 1. Left Col: Location & Alerts
        self.location_and_alert_container = self._create_location_alert_card()
        
        # 2. Middle Col: Sensor Cards
        cards_container = self._create_sensor_cards()
        
        # 3. Right Col: Map
        self.map_card = MapWidget()
        
        # 4. Bottom Row: Graph
        self.graph_container = self._create_graph_container()
        
        # Assemble Grid
        self.main_layout.addWidget(self.location_and_alert_container, 0, 0)
        self.main_layout.addWidget(cards_container, 0, 1)
        self.main_layout.addWidget(self.map_card, 0, 2)
        self.main_layout.addWidget(self.graph_container, 1, 0, 1, 3)
        
        # Grid Ratios
        self.main_layout.setColumnStretch(0, 3)
        self.main_layout.setColumnStretch(1, 5)
        self.main_layout.setColumnStretch(2, 4)
        self.main_layout.setRowStretch(0, 1)
        self.main_layout.setRowStretch(1, 2)
        
        self._apply_shadows()

    def _create_location_alert_card(self):
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(15)
        
        loc_card = QWidget()
        loc_card.setObjectName("card")
        loc_layout = QVBoxLayout(loc_card)
        
        title_label = QLabel("📍 ACTIVE HELMET LOCATION")
        title_label.setObjectName("cardTitle")
        loc_layout.addWidget(title_label)
        
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Lat Card
        lat_card = QWidget()
        lat_card.setObjectName("locationInfoCard")
        lat_layout = QVBoxLayout(lat_card)
        lat_layout.setContentsMargins(20, 15, 20, 15)
        lat_title = QLabel("LATITUDE")
        lat_title.setObjectName("locationCardSubTitle")
        self.main_latitude_label = QLabel("---")
        self.main_latitude_label.setObjectName("locationCardValue")
        lat_layout.addWidget(lat_title)
        lat_layout.addWidget(self.main_latitude_label)
        lat_layout.addStretch()
        grid.addWidget(lat_card, 0, 0)
        
        # Lon Card
        lon_card = QWidget()
        lon_card.setObjectName("locationInfoCard")
        lon_layout = QVBoxLayout(lon_card)
        lon_layout.setContentsMargins(20, 15, 20, 15)
        lon_title = QLabel("LONGITUDE")
        lon_title.setObjectName("locationCardSubTitle")
        self.main_longitude_label = QLabel("---")
        self.main_longitude_label.setObjectName("locationCardValue")
        lon_layout.addWidget(lon_title)
        lon_layout.addWidget(self.main_longitude_label)
        lon_layout.addStretch()
        grid.addWidget(lon_card, 0, 1)
        
        loc_layout.addLayout(grid)
        
        self.alert_panel = LiveAlertPanel()
        
        container_layout.addWidget(loc_card)
        container_layout.addWidget(self.alert_panel, 1)
        return container

    def _create_sensor_cards(self):
        container = QWidget()
        layout = QGridLayout(container)
        layout.setSpacing(15)
        
        self.co_card = self._create_card("CO Level", "ppm", "pTasksCard", is_float=False)
        self.temp_card = self._create_card("Temperature", "°C", "aTasksCard", is_float=True)
        self.humidity_card = self._create_card("Humidity", "%", "humidityCard", is_float=True)
        self.status_card = self._create_status_card()
        self.battery_card = BatteryCard()
        self.methane_card = self._create_card("CH₄ (Methane)", "% LEL", "methaneCard", is_float=False)
        self.nat_gas_card = self._create_card("LPG (Natural Gas)", "% LEL", "natGasCard", is_float=False)

        layout.addWidget(self.co_card, 0, 0, 1, 2) 
        layout.addWidget(self.status_card, 0, 2)
        layout.addWidget(self.methane_card, 1, 0)
        layout.addWidget(self.nat_gas_card, 1, 1)
        layout.addWidget(self.battery_card, 1, 2)
        layout.addWidget(self.temp_card, 2, 0)
        layout.addWidget(self.humidity_card, 2, 1)
        
        return container

    def _create_card(self, title, unit, name, is_float):
        card = QWidget()
        card.setObjectName(name)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 20, 25, 20)
        
        title_label = QLabel(title)
        title_label.setObjectName("dataCardTitle")
        
        # --- Correctly using the global import ---
        value_layout = QHBoxLayout()
        
        val_label = AnimatedLabel(is_float=is_float)
        val_label.setObjectName("dataCardValue")
        
        unit_label = QLabel(unit)
        unit_label.setObjectName("dataCardUnit")
        
        value_layout.addStretch(1)
        value_layout.addWidget(val_label)
        value_layout.addWidget(unit_label, 0, Qt.AlignTop)
        value_layout.addStretch(1)
        
        layout.addWidget(title_label, 0, Qt.AlignTop)
        layout.addStretch(1)
        layout.addLayout(value_layout)
        layout.addStretch(1)
        
        card.value_label = val_label
        return card

    def _create_status_card(self):
        card = QWidget()
        card.setObjectName("statusCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("SYSTEM STATUS")
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        self.gps_status_label = QLabel("Unknown")
        self.gps_status_label.setObjectName("statusLabel")
        self.co_status_label = QLabel("Unknown")
        self.co_status_label.setObjectName("statusLabel")
        
        form_layout.addRow(QLabel("GPS Signal:"), self.gps_status_label)
        form_layout.addRow(QLabel("CO Alert:"), self.co_status_label)
        
        layout.addLayout(form_layout)
        return card

    def _create_graph_container(self):
        container = QWidget()
        container.setObjectName("card")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(5)
        
        header = QHBoxLayout()
        title = QLabel("SENSOR ANALYSIS HISTORY")
        title.setObjectName("cardTitle")
        
        legend = QHBoxLayout()
        legend.setSpacing(15)
        legend.addWidget(self._create_legend_item("#2dd4bf", "CO Safe"))
        legend.addWidget(self._create_legend_item("#ef4444", "CO Danger"))
        legend.addWidget(self._create_legend_item("#a3e635", "Methane"))
        legend.addWidget(self._create_legend_item("#f472b6", "Nat. Gas"))
        legend.addWidget(self._create_legend_item("#3b82f6", "Temp"))
        legend.addWidget(self._create_legend_item("#f97316", "Hum"))
        
        header.addWidget(title)
        header.addStretch()
        header.addLayout(legend)
        
        self.graph_canvas = FocusGraphCanvas()
        layout.addLayout(header)
        layout.addWidget(self.graph_canvas)
        return container

    def _create_legend_item(self, color, text):
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setSpacing(8)
        box = QLabel()
        box.setFixedSize(12, 12)
        box.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
        layout.addWidget(box)
        layout.addWidget(QLabel(text))
        return item

    def _apply_shadows(self):
        widgets = [
            self.location_and_alert_container, self.co_card, self.temp_card,
            self.humidity_card, self.status_card, self.graph_container,
            self.map_card, self.battery_card, self.alert_panel,
            self.methane_card, self.nat_gas_card
        ]
        for w in widgets:
            if w:
                shadow = QGraphicsDropShadowEffect(self)
                shadow.setBlurRadius(50)
                shadow.setOffset(0, 8)
                shadow.setColor(QColor(0, 0, 0, 80))
                w.setGraphicsEffect(shadow)