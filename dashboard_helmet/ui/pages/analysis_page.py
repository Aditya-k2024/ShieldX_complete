import csv
from collections import deque
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, 
    QTableView, QHeaderView, QFileDialog
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt

# Local Imports
from config import MAX_POINTS
from ui.components.graphs import SingleMetricGraphCanvas
from ui.components.cards import StatCard
from ui.components.shared import HoverButton

class HistoricalAnalysisPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_layout = QHBoxLayout(self) 
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # --- LEFT SIDE: Graphs + Table ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(15)
        
        # 1. Graphs Grid
        graph_container = QWidget()
        graph_layout = QGridLayout(graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(15)
        
        self.co_graph = SingleMetricGraphCanvas("CO (Gas) Trend", "gas", "#ef4444", "ppm")
        self.methane_graph = SingleMetricGraphCanvas("CH₄ (Methane) Trend", "methane", "#a3e635", "%LEL")
        self.nat_gas_graph = SingleMetricGraphCanvas("LPG (Natural Gas) Trend", "natural_gas", "#f472b6", "%LEL")
        self.temp_graph = SingleMetricGraphCanvas("Temperature Trend", "temperature", "#f97316", "°C")
        self.hum_graph = SingleMetricGraphCanvas("Humidity Trend", "humidity", "#3b82f6", "%")
        
        graph_layout.addWidget(self.co_graph, 0, 0)
        graph_layout.addWidget(self.methane_graph, 0, 1)
        graph_layout.addWidget(self.nat_gas_graph, 0, 2)
        graph_layout.addWidget(self.temp_graph, 1, 0)
        graph_layout.addWidget(self.hum_graph, 1, 1)
        
        left_layout.addWidget(graph_container, 3)

        # 2. Table
        title = QLabel("Full Data History")
        title.setObjectName("cardTitle")
        left_layout.addWidget(title)
        
        self.table_view = QTableView()
        self.table_model = QStandardItemModel()
        self.table_view.setModel(self.table_model)
        self.table_view.setStyleSheet("""
            QTableView { background-color: #27272a; border: none; gridline-color: #444; font-size: 10pt; }
            QTableView::item { padding: 5px; }
            QHeaderView::section { background-color: #333; color: #FFF; padding: 8px; border: none; }
        """)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.table_view, 2)
        
        self.main_layout.addWidget(left_container, 3)

        # --- RIGHT SIDE: Insights Panel ---
        right_container = QWidget()
        right_container.setFixedWidth(240) 
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        
        right_layout.addWidget(QLabel("SESSION PEAKS", objectName="cardTitle"))
        
        self.peak_co_card = StatCard("Peak CO Level", "ppm", "#ef4444")
        self.peak_temp_card = StatCard("Max Temperature", "°C", "#f97316")
        self.low_batt_card = StatCard("Lowest Battery", "%", "#2dd4bf")
        
        right_layout.addWidget(self.peak_co_card)
        right_layout.addWidget(self.peak_temp_card)
        right_layout.addWidget(self.low_batt_card)
        
        right_layout.addStretch()
        
        export_btn = HoverButton("camera", "Export CSV")
        export_btn.clicked.connect(self.export_to_csv)
        right_layout.addWidget(export_btn)
        
        self.main_layout.addWidget(right_container, 0) 
        
        self.all_data_cache = [] 
        
    def update_data(self, all_helmet_data, current_helmet_id):
        current_data = all_helmet_data.get(current_helmet_id, deque(maxlen=MAX_POINTS))
        
        # Update Graphs
        self.co_graph.update_plot(current_data)
        self.methane_graph.update_plot(current_data) 
        self.nat_gas_graph.update_plot(current_data)
        self.temp_graph.update_plot(current_data)
        self.hum_graph.update_plot(current_data)
        
        if current_data:
            # Find Peaks
            max_co = max((d['gas'] for d in current_data), default=0)
            self.peak_co_card.update_value(f"{max_co:.0f}")
            
            max_temp = max((d['temperature'] for d in current_data), default=0)
            self.peak_temp_card.update_value(f"{max_temp:.1f}")
            
            min_batt = min((d['battery'] for d in current_data), default=0)
            self.low_batt_card.update_value(f"{min_batt}")

        # Update Table
        all_data_points = []
        for helmet_id, data_deque in all_helmet_data.items():
            for data_point in data_deque:
                all_data_points.append(data_point)
        
        try:
            sorted_data = sorted(all_data_points, key=lambda x: x['timestamp'], reverse=True)
        except:
            sorted_data = all_data_points
            
        if sorted_data == self.all_data_cache:
            return
            
        self.all_data_cache = sorted_data
        
        self.table_model.clear()
        header = ["Time", "ID", "CO", "CH4", "LPG", "Temp", "Hum", "Bat", "Lat", "Lng"]
        self.table_model.setHorizontalHeaderLabels(header)
        
        for data in sorted_data:
            row = [
                QStandardItem(data.get('timestamp', 'N/A')),
                QStandardItem(data.get('helmetId', 'N/A')),
                QStandardItem(f"{data.get('gas', 0):.0f}"),
                QStandardItem(f"{data.get('methane', 0)}"), 
                QStandardItem(f"{data.get('natural_gas', 0)}"),
                QStandardItem(f"{data.get('temperature', 0):.1f}"),
                QStandardItem(f"{data.get('humidity', 0):.1f}"),
                QStandardItem(f"{data.get('battery', 0)}%"),
                QStandardItem(f"{data.get('latitude', 0):.4f}"),
                QStandardItem(f"{data.get('longitude', 0):.4f}"),
            ]
            for item in row: item.setEditable(False)
            self.table_model.appendRow(row)

    def export_to_csv(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Report", "safety_report.csv", "CSV Files (*.csv)")
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    headers = ["Timestamp", "Helmet ID", "CO", "Methane", "Nat Gas", "Temp", "Humidity", "Battery", "Lat", "Lng"]
                    writer.writerow(headers)
                    for item in self.all_data_cache:
                        writer.writerow([
                            item.get('timestamp'), item.get('helmetId'), 
                            item.get('gas'), item.get('methane'), item.get('natural_gas'),
                            item.get('temperature'), item.get('humidity'), 
                            item.get('battery'), item.get('latitude'), item.get('longitude')
                        ])
                print(f"Exported to {filename}")
            except Exception as e:
                print(f"Export failed: {e}")