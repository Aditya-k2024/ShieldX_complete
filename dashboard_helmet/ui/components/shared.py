import os
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property, QSize, QRectF
)
from PySide6.QtGui import (
    QIcon, QPainter, QPainterPath, QPen, QColor, QPixmap
)
from PySide6.QtWidgets import (
    QPushButton, QLabel, QSizePolicy
)

# --- 1. Animated Label (For smooth number transitions) ---
class AnimatedLabel(QLabel):
    def __init__(self, is_float=False, parent=None):
        super().__init__("0", parent)
        self._is_float = is_float
        self._value = 0.0
        self.animation = QPropertyAnimation(self, b"value", self)
        self.animation.setDuration(400)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

    @Property(float)
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        self.setText(f"{new_value:.1f}" if self._is_float else f"{int(new_value)}")

    def animate_to_value(self, end_value):
        self.animation.setEndValue(end_value)
        self.animation.start()


# --- 2. Icon Factory (Draws vector icons via code) ---
class IconFactory:
    @staticmethod
    def get(name, color="#E0E0E0"):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(color))
        pen.setWidth(2)
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        if name == "dashboard":
            # 4 squares
            painter.drawRoundedRect(2, 2, 8, 8, 2, 2)
            painter.drawRoundedRect(14, 2, 8, 8, 2, 2)
            painter.drawRoundedRect(2, 14, 8, 8, 2, 2)
            painter.drawRoundedRect(14, 14, 8, 8, 2, 2)
            
        elif name == "warehouse":
            # Database stack
            painter.drawEllipse(4, 2, 16, 6)
            path = QPainterPath()
            path.moveTo(4, 5)
            path.lineTo(4, 12)
            path.cubicTo(4, 16, 20, 16, 20, 12)
            path.lineTo(20, 5)
            painter.drawPath(path)
            path2 = QPainterPath()
            path2.moveTo(4, 12)
            path2.lineTo(4, 19)
            path2.cubicTo(4, 23, 20, 23, 20, 19)
            path2.lineTo(20, 12)
            painter.drawPath(path2)

        elif name == "analysis":
            # Zigzag graph
            path = QPainterPath()
            path.moveTo(2, 20)
            path.lineTo(8, 12)
            path.lineTo(14, 16)
            path.lineTo(22, 4)
            painter.drawPath(path)
            # Arrow head
            painter.drawLine(22, 4, 18, 4)
            painter.drawLine(22, 4, 22, 8)

        elif name == "map":
            # Pin
            painter.drawEllipse(7, 2, 10, 10)
            path = QPainterPath()
            path.moveTo(7, 7)
            path.lineTo(12, 22)
            path.lineTo(17, 7)
            painter.drawPath(path)
            painter.drawPoint(12, 7)

        elif name == "settings":
            # Gear/Slider representation
            painter.drawRoundedRect(2, 4, 20, 4, 2, 2)
            painter.drawRoundedRect(2, 16, 20, 4, 2, 2)
            painter.setBrush(QColor(color))
            painter.drawEllipse(6, 3, 6, 6)
            painter.drawEllipse(12, 15, 6, 6)

        elif name == "pause":
            painter.drawLine(8, 4, 8, 20)
            painter.drawLine(16, 4, 16, 20)
            
        elif name == "camera":
            painter.drawRoundedRect(2, 6, 20, 14, 3, 3)
            painter.drawEllipse(9, 10, 6, 6)
            painter.drawLine(16, 3, 20, 3) # Flash/Top part

        elif name == "menu":
            painter.drawLine(4, 6, 20, 6)
            painter.drawLine(4, 12, 20, 12)
            painter.drawLine(4, 18, 20, 18)
            
        elif name == "close":
            painter.drawLine(6, 6, 18, 18)
            painter.drawLine(18, 6, 6, 18)

        painter.end()
        return QIcon(pixmap)


# --- 3. Hover Button (Generic Button) ---
class HoverButton(QPushButton):
    def __init__(self, icon_name="", text="", parent=None):
        super().__init__(text, parent)
        
        # If icon_name is provided, try to get it from factory
        if icon_name:
            self.setIcon(IconFactory.get(icon_name))
            self.setIconSize(self.sizeHint().boundedTo(self.size()*0.6))
            
        self.setStyleSheet("""
            QPushButton { 
                background-color: #27272a; 
                color: #E0E0E0; 
                border: none; 
                padding: 10px 15px; 
                font-size: 11pt; 
                font-weight: 600; 
                border-radius: 12px;
            }
            QPushButton:hover { 
                background-color: #3f3f46; 
            }
            QPushButton:pressed { 
                background-color: #52525b; 
            }
            QPushButton:checked {
                background-color: #1d4ed8;
                color: white;
            }
        """)


# --- 4. Sidebar Button (Collapsible) ---
class SidebarButton(QPushButton):
    def __init__(self, icon_name, label_text, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.label_text = label_text
        self.is_collapsed = True
        
        # Load Custom Icon from Factory
        self.setIcon(IconFactory.get(icon_name))
        self.setIconSize(self.sizeHint().boundedTo(self.size()*0.6))
        
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(50)

    def update_mode(self, collapsed):
        self.is_collapsed = collapsed
        if collapsed:
            self.setText("") # No text in collapsed mode
            self.setToolTip(self.label_text)
        else:
            self.setText(f"  {self.label_text}") # Add text with padding
            self.setToolTip("")