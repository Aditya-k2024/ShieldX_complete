from PySide6.QtCore import Qt, QRectF, Slot
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QStackedWidget
)

# --- 1. Stat Card (Used in Analysis Page) ---
class StatCard(QFrame):
    def __init__(self, title, unit, color, parent=None):
        super().__init__(parent)
        self.unit = unit
        self.color = color
        
        # Styling
        self.setObjectName("statCard")
        self.setStyleSheet(f"""
            #statCard {{
                background-color: #27272a;
                border-radius: 12px;
                border-left: 4px solid {color};
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #A1A1AA; font-size: 9pt; font-weight: 600; text-transform: uppercase;")
        layout.addWidget(title_lbl)
        
        # Value Row
        row = QHBoxLayout()
        self.value_lbl = QLabel("0")
        self.value_lbl.setStyleSheet("color: #FFFFFF; font-size: 22pt; font-weight: 700;")
        
        unit_lbl = QLabel(unit)
        unit_lbl.setStyleSheet(f"color: {color}; font-size: 10pt; font-weight: 600; margin-bottom: 4px;")
        
        row.addWidget(self.value_lbl)
        row.addWidget(unit_lbl, 0, Qt.AlignmentFlag.AlignBottom)
        row.addStretch()
        
        layout.addLayout(row)

    def update_value(self, value):
        self.value_lbl.setText(f"{value}")


# --- 2. Battery Card (Visual Battery Indicator) ---
class BatteryCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedSize(200, 100)
        self._level = 0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.value_label = QLabel("-- %")
        self.value_label.setObjectName("batteryValue")
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_level(self, level):
        self._level = level
        self.value_label.setText(f"{level} %")
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Battery Body
        body_rect = QRectF(self.width() - 60, 20, 50, 25)
        painter.setPen(QPen(QColor("#9E9E9E"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(body_rect, 5, 5)
        
        # Draw Tip
        tip_rect = QRectF(body_rect.right(), 25, 5, 15)
        painter.setBrush(QColor("#9E9E9E"))
        painter.drawRoundedRect(tip_rect, 2, 2)
        
        # Determine Color based on Level
        if self._level > 50:
            fill_color = QColor("#2dd4bf") # Teal
        elif self._level > 20:
            fill_color = QColor("#facc15") # Yellow
        else:
            fill_color = QColor("#ef4444") # Red
        
        # Draw Fill Level
        fill_width = (body_rect.width() - 6) * (self._level / 100.0)
        fill_rect = QRectF(body_rect.left() + 3, body_rect.top() + 3, fill_width, body_rect.height() - 6)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(fill_color)
        painter.drawRoundedRect(fill_rect, 3, 3)


# --- 3. Alert Item Widget (Individual row in the alert list) ---
class AlertItemWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        self.icon_label = QLabel("!")
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("""
            background-color: #ef4444; 
            color: white; 
            font-size: 20px; 
            font-weight: bold; 
            border-radius: 16px;
        """)
        layout.addWidget(self.icon_label)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        
        self.helmet_id_label = QLabel("SH-000")
        self.helmet_id_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #FFFFFF;")
        info_layout.addWidget(self.helmet_id_label)
        
        details_layout = QHBoxLayout()
        self.gas_label = QLabel("CO: 0000 ppm")
        self.gas_label.setStyleSheet("font-size: 10pt; color: #ef4444; font-weight: bold;")
        
        self.loc_label = QLabel("Loc: 00.00, 00.00")
        self.loc_label.setStyleSheet("font-size: 9pt; color: #9E9E9E;")
        
        details_layout.addWidget(self.gas_label)
        details_layout.addStretch()
        details_layout.addWidget(self.loc_label)
        
        info_layout.addLayout(details_layout)
        layout.addLayout(info_layout, 1)

    def update_data(self, helmet_id, gas_level, lat, lng):
        self.helmet_id_label.setText(helmet_id)
        self.gas_label.setText(f"Val: {gas_level:.0f}")
        self.loc_label.setText(f"Loc: {lat:.4f}, {lng:.4f}")


# --- 4. Live Alert Panel (The list container) ---
class LiveAlertPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.set_alert_state(False)
        self.items = {}
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("🚨 LIVE ALERTS")
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        
        self.stack = QStackedWidget()
        
        self.alert_list = QListWidget()
        self.alert_list.setStyleSheet("""
            QListWidget { 
                background-color: transparent; 
                border: none;
            }
            QListWidget::item { 
                border-bottom: 1px solid #333;
                padding: 2px 0px;
            }
        """)
        
        self.placeholder_label = QLabel("No Active Alerts")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("font-size: 11pt; color: #9E9E9E; font-style: italic;")
        
        self.stack.addWidget(self.alert_list)
        self.stack.addWidget(self.placeholder_label)
        layout.addWidget(self.stack, 1)
        
        self._check_empty()

    def _check_empty(self):
        if self.alert_list.count() == 0:
            self.stack.setCurrentWidget(self.placeholder_label)
        else:
            self.stack.setCurrentWidget(self.alert_list)

    @Slot(str, float, float, float)
    def add_or_update_alert(self, helmet_id, gas_level, lat, lng):
        if helmet_id in self.items:
            widget = self.items[helmet_id]["widget"]
            widget.update_data(helmet_id, gas_level, lat, lng)
        else:
            item = QListWidgetItem()
            widget = AlertItemWidget()
            widget.update_data(helmet_id, gas_level, lat, lng)
            item.setSizeHint(widget.sizeHint())
            
            self.alert_list.insertItem(0, item)
            self.alert_list.setItemWidget(item, widget)
            self.items[helmet_id] = {"item": item, "widget": widget}
        self._check_empty()

    @Slot(str)
    def remove_alert(self, helmet_id):
        if helmet_id in self.items:
            item = self.items[helmet_id]["item"]
            row = self.alert_list.row(item)
            self.alert_list.takeItem(row)
            del self.items[helmet_id]
        self._check_empty()
                
    @Slot(bool)
    def set_alert_state(self, is_alerting):
        if is_alerting:
            self.setStyleSheet("#card { background-color: #1F1F1F; border-radius: 16px; border: 2px solid #ef4444; }")
        else:
            self.setStyleSheet("#card { background-color: #1F1F1F; border-radius: 16px; border: 2px solid #1F1F1F; }")