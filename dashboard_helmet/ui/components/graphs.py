from collections import deque
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen, QFont, QBrush, QPolygonF
from PySide6.QtCore import Qt, QPointF, QRectF

# Import Global Config
from config import MAX_POINTS

class BaseGraphCanvas(QWidget):
    """
    A base class for plotting graphs. Contains shared drawing logic.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(200)
        self.background_color = QColor("#1F1F1F")
        self.padding = {'left': 45, 'right': 15, 'top': 35, 'bottom': 25} 
        self.grid_pen = QPen(QColor("#444444"), 0.5, Qt.PenStyle.DashLine)
        self.axis_pen = QPen(QColor("#9E9E9E"))
        self.axis_font = QFont("Segoe UI", 8)
        self.title_font = QFont("Segoe UI", 11, QFont.Weight.Bold)

    def get_points(self, graph_rect, max_val, values):
        """
        Dynamic Stretch Logic:
        Stretches points to fill width, but relies on MAX_POINTS to stop compression.
        """
        if not values:
            return []
        
        points = []
        num_points = len(values)
        
        if num_points < 2:
             x = graph_rect.left()
             y = graph_rect.top() + graph_rect.height() * (1 - values[0] / max_val)
             return [QPointF(x, y)]

        step_x = graph_rect.width() / (num_points - 1)

        for i, v in enumerate(values):
            x = graph_rect.left() + (i * step_x)
            y = graph_rect.top() + graph_rect.height() * (1 - v / max_val)
            points.append(QPointF(x, y))
            
        return points

    def draw_line_and_fill(self, painter, max_val, graph_rect, values, color, thickness):
        if len(values) < 2:
            return 
            
        points = self.get_points(graph_rect, max_val, values)
        line_path = QPainterPath()
        line_path.moveTo(points[0])
        
        # Bezier Curve Smoothing
        for i in range(len(points) - 1):
            ctrl_pt1 = QPointF((points[i].x() + points[i+1].x()) / 2, points[i].y())
            ctrl_pt2 = QPointF((points[i].x() + points[i+1].x()) / 2, points[i+1].y())
            line_path.cubicTo(ctrl_pt1, ctrl_pt2, points[i+1])
            
        fill_path = QPainterPath(line_path)
        fill_path.lineTo(points[-1].x(), graph_rect.bottom())
        fill_path.lineTo(points[0].x(), graph_rect.bottom())
        fill_path.closeSubpath()
        
        fill_color = QColor(color)
        fill_color.setAlphaF(0.2)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(fill_path)
        
        pen = QPen(color, thickness)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line_path)

    def draw_grid_and_axes(self, painter, graph_rect, max_val):
        painter.setFont(self.axis_font)
        for i in range(6): # 0, 2, 4, 6, 8, 10
            y = graph_rect.top() + graph_rect.height() * i / 5.0
            value = max_val * (1 - i / 5.0)
            
            painter.setPen(self.grid_pen)
            painter.drawLine(graph_rect.left(), y, graph_rect.right(), y)
            
            painter.setPen(self.axis_pen)
            painter.drawText(QRectF(0, y - 10, self.padding['left'] - 5, 20), Qt.AlignRight | Qt.AlignVCenter, f"{value:.0f}")

        painter.setPen(self.axis_pen)
        painter.drawText(QRectF(graph_rect.left(), graph_rect.bottom(), 40, self.padding['bottom']), Qt.AlignLeft | Qt.AlignVCenter, "Oldest")
        painter.drawText(QRectF(graph_rect.right() - 40, graph_rect.bottom(), 40, self.padding['bottom']), Qt.AlignRight | Qt.AlignVCenter, "Latest")


class FocusGraphCanvas(BaseGraphCanvas):
    """
    The main multi-line graph shown on the Dashboard page.
    Plots CO, Temp, Humidity, Methane, and Natural Gas simultaneously.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.padding['top'] = 5 
        self.threshold = 900
        
        # Data Storage
        self.focus_vals = deque(maxlen=MAX_POINTS)       # CO
        self.distraction_vals = deque(maxlen=MAX_POINTS) # Temperature
        self.humidity_vals = deque(maxlen=MAX_POINTS)    # Humidity
        self.methane_vals = deque(maxlen=MAX_POINTS)     # Methane
        self.nat_gas_vals = deque(maxlen=MAX_POINTS)     # Natural Gas
        
        # Colors
        self.co_normal_color = QColor("#2dd4bf")         # Teal
        self.co_danger_color = QColor("#ef4444")         # Red
        self.temp_color = QColor("#3b82f6")              # Blue
        self.humidity_color = QColor("#f97316")          # Orange
        self.methane_color = QColor("#a3e635")           # Lime Green
        self.nat_gas_color = QColor("#f472b6")           # Pink
        
    def set_threshold(self, new_threshold):
        self.threshold = new_threshold
        self.update()

    def update_plot(self, data_deque):
        if not data_deque:
            self.focus_vals.clear()
            self.distraction_vals.clear()
            self.humidity_vals.clear()
            self.methane_vals.clear()
            self.nat_gas_vals.clear()
            self.update()
            return
        
        # Extract data from deque
        self.focus_vals = deque((d['gas'] for d in data_deque), maxlen=MAX_POINTS)
        self.distraction_vals = deque((d['temperature'] for d in data_deque), maxlen=MAX_POINTS)
        self.humidity_vals = deque((d['humidity'] for d in data_deque), maxlen=MAX_POINTS)
        self.methane_vals = deque((d['methane'] for d in data_deque), maxlen=MAX_POINTS)
        self.nat_gas_vals = deque((d['natural_gas'] for d in data_deque), maxlen=MAX_POINTS)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.background_color)
        
        if not self.focus_vals: 
            return
            
        graph_rect = self.rect().adjusted(self.padding['left'], self.padding['top'], -self.padding['right'], -self.padding['bottom'])
        
        # Calculate Max Value for Y-Axis Scaling
        max_val = max(
            max(self.focus_vals, default=0),
            max(self.distraction_vals, default=0),
            max(self.humidity_vals, default=0),
            max(self.methane_vals, default=0),
            max(self.nat_gas_vals, default=0),
            self.threshold
        ) * 1.1
        
        if max_val < 1: max_val = 1
            
        self.draw_grid_and_axes(painter, graph_rect, max_val)

        # Draw Threshold Line
        if max_val > self.threshold:
            y_threshold = graph_rect.top() + graph_rect.height() * (1 - self.threshold / max_val)
            threshold_pen = QPen(self.co_danger_color, 1.5, Qt.PenStyle.DashLine)
            painter.setPen(threshold_pen)
            painter.drawLine(graph_rect.left(), y_threshold, graph_rect.right(), y_threshold)
            painter.setFont(QFont("Segoe UI", 8))
            painter.setPen(self.co_danger_color)
            painter.drawText(QRectF(graph_rect.right() - 110, y_threshold - 5, 110, 20), Qt.AlignLeft, f"CO Limit: {self.threshold} ppm")
            
        line_thickness = 2.5 
        
        # Draw Lines (Order matters: First drawn is behind)
        self.draw_line_and_fill(painter, max_val, graph_rect, self.distraction_vals, self.temp_color, line_thickness)
        self.draw_line_and_fill(painter, max_val, graph_rect, self.humidity_vals, self.humidity_color, line_thickness)
        self.draw_line_and_fill(painter, max_val, graph_rect, self.methane_vals, self.methane_color, line_thickness)
        self.draw_line_and_fill(painter, max_val, graph_rect, self.nat_gas_vals, self.nat_gas_color, line_thickness)
        
        # Draw CO (Segmented) last so it stays on top
        self.draw_segmented_co_line(painter, max_val, graph_rect, self.focus_vals, line_thickness + 1)

    def draw_segmented_co_line(self, painter, max_val, graph_rect, values, thickness):
        if len(values) < 2: 
            return
            
        green_pen = QPen(self.co_normal_color, thickness)
        green_pen.setCapStyle(Qt.RoundCap)
        red_pen = QPen(self.co_danger_color, thickness)
        red_pen.setCapStyle(Qt.RoundCap)
        green_brush = QBrush(QColor(45, 212, 191, 51))
        red_brush = QBrush(QColor(239, 68, 68, 51))
        
        points = self.get_points(graph_rect, max_val, values)
        path_segment = QPainterPath()
        
        for i in range(len(points) - 1):
            is_danger = values[i] > self.threshold or values[i+1] > self.threshold
            pen = red_pen if is_danger else green_pen
            brush = red_brush if is_danger else green_brush
            
            fill_poly = QPolygonF([points[i], points[i+1], QPointF(points[i+1].x(), graph_rect.bottom()), QPointF(points[i].x(), graph_rect.bottom())])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(brush)
            painter.drawPolygon(fill_poly)
            
            path_segment.moveTo(points[i])
            ctrl_pt1 = QPointF((points[i].x() + points[i+1].x()) / 2, points[i].y())
            ctrl_pt2 = QPointF((points[i].x() + points[i+1].x()) / 2, points[i+1].y())
            path_segment.cubicTo(ctrl_pt1, ctrl_pt2, points[i+1])
            painter.strokePath(path_segment, pen)
            path_segment.clear()


class SingleMetricGraphCanvas(BaseGraphCanvas):
    """
    A graph widget that plots a single metric. Used in the Analysis page.
    """
    def __init__(self, title, metric_key, color, unit, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.title = title
        self.metric_key = metric_key
        self.color = QColor(color)
        self.unit = unit
        self.data_deque = deque(maxlen=MAX_POINTS)

    def update_plot(self, data_deque):
        if not data_deque:
            self.data_deque.clear()
        else:
            self.data_deque = deque((d[self.metric_key] for d in data_deque), maxlen=MAX_POINTS)
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.background_color)
        
        # Draw Title
        painter.setPen(self.axis_pen)
        painter.setFont(self.title_font)
        painter.drawText(QRectF(self.padding['left'], 5, self.width(), self.padding['top']), Qt.AlignLeft | Qt.AlignVCenter, self.title)

        if not self.data_deque:
            painter.setPen(self.axis_pen)
            painter.setFont(self.title_font)
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data for Selected Helmet")
            return
            
        graph_rect = self.rect().adjusted(self.padding['left'], self.padding['top'], -self.padding['right'], -self.padding['bottom'])
        
        max_val = max(self.data_deque, default=0) * 1.1
        if max_val < 1: 
            max_val = 1
            
        self.draw_grid_and_axes(painter, graph_rect, max_val)
        self.draw_line_and_fill(painter, max_val, graph_rect, self.data_deque, self.color, 3.5)