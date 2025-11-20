import os
import sys
from collections import deque
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, 
    QLabel, QGraphicsDropShadowEffect, QPushButton
)
from PySide6.QtCore import QTimer, Slot, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPainterPath, QLinearGradient, QColor, QPen, Qt

# --- LOCAL IMPORTS ---
from config import (
    API_KEY, CITY, MAX_POINTS, DEFAULT_BAUD_RATE, 
    DEFAULT_CO_THRESHOLD, DEFAULT_METHANE_THRESHOLD, DEFAULT_LPG_THRESHOLD
)
from workers.serial_workers import SerialWorker
from workers.weather_worker import WeatherWorker

# Components
from ui.components.shared import HoverButton, SidebarButton, IconFactory

# Pages
from ui.pages.dashboard_page import DashboardPage
from ui.pages.warehouse_page import DataWarehousePage
from ui.pages.analysis_page import HistoricalAnalysisPage
from ui.pages.fleet_map_page import FleetMapPage
from ui.pages.settings_page import SettingsPage

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.sidebar_collapsed_width = 70
        self.sidebar_expanded_width = 240
        self.is_sidebar_expanded = False 

        # --- 1. SET WINDOW ICON ---
        if os.path.exists("logo.png"):
            self.setWindowIcon(QIcon("logo.png"))
        else:
            self.setWindowIcon(IconFactory.get("dashboard", "#2dd4bf"))

        self.setWindowTitle("ShieldX - Real-Time IoT Monitor (Serial Mode)")
        self.setGeometry(100, 100, 1400, 900)
        
        # Data Containers
        self.helmet_data = {}
        self.current_helmet_id = None
        self.helmets_in_alert = set()
        
        # Thresholds (Initialize with Defaults from Config)
        self.co_threshold = DEFAULT_CO_THRESHOLD
        self.methane_threshold = DEFAULT_METHANE_THRESHOLD
        self.lpg_threshold = DEFAULT_LPG_THRESHOLD

        self._setup_ui()
        self._apply_stylesheet()

        # --- SETUP WORKERS ---
        self.serial_worker = SerialWorker(baud_rate=DEFAULT_BAUD_RATE)
        self.serial_worker.data_received.connect(self.process_sensor_data)
        self.serial_worker.start()

        self.weather_worker = WeatherWorker(API_KEY, CITY)
        self.weather_worker.start()

        # Timers
        self.header_timer = QTimer(self)
        self.header_timer.timeout.connect(self.update_header_time)
        self.header_timer.start(1000)

    # --- CORE DATA LOGIC ---
    @Slot(dict)
    def process_sensor_data(self, raw_data):
        # 1. Normalize Data
        try:
            typed_data = {
                "helmetId": raw_data.get('helmetId', 'Unknown'),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "gas": float(raw_data.get("gas", 0)),           # CO
                "methane": float(raw_data.get("methane", 0)),   # CH4
                "natural_gas": float(raw_data.get("natural_gas", 0)), # LPG
                "temperature": float(raw_data.get("temperature", 0)),
                "humidity": float(raw_data.get("humidity", 0)),
                "latitude": float(raw_data.get("latitude", 0.0)),
                "longitude": float(raw_data.get("longitude", 0.0)),
                "battery": int(raw_data.get("battery", 0)),
                "emergency": str(raw_data.get("emergency", "false")).lower() == "true"
            }
        except ValueError as e:
            print(f"Data conversion error: {e}")
            return

        helmet_id = typed_data['helmetId']
        
        if self.current_helmet_id is None:
            self.current_helmet_id = helmet_id
            self.helmet_id_label.setText(f"ID: {helmet_id}")

        if helmet_id not in self.helmet_data:
            self.helmet_data[helmet_id] = deque(maxlen=MAX_POINTS)
        self.helmet_data[helmet_id].append(typed_data)

        # --- MULTI-GAS ALERT LOGIC ---
        co_val = typed_data['gas']
        meth_val = typed_data['methane']
        lpg_val = typed_data['natural_gas']
        
        alert_type = None
        trigger_value = 0
        
        if co_val > self.co_threshold:
            alert_type = "HIGH CO (TOXIC)"
            trigger_value = co_val
        elif meth_val > self.methane_threshold:
            alert_type = "HIGH METHANE"
            trigger_value = meth_val
        elif lpg_val > self.lpg_threshold:
            alert_type = "HIGH LPG LEAK"
            trigger_value = lpg_val

        if alert_type:
            # Trigger Hardware Alarm
            self.serial_worker.send_command('1')

            print(f"🚨 ALERT: {alert_type} - {trigger_value}")
            self.data_warehouse_page.historical_log.add_alert(typed_data)
            
            if helmet_id not in self.helmets_in_alert:
                self.helmets_in_alert.add(helmet_id)
                self.dashboard_page.alert_panel.set_alert_state(True)
            
            self.dashboard_page.alert_panel.add_or_update_alert(
                helmet_id, trigger_value, typed_data['latitude'], typed_data['longitude']
            )
            self.dashboard_page.co_status_label.setText(alert_type)
            self.dashboard_page.co_status_label.setStyleSheet("color: #ef4444; font-weight: bold;")

        else:
            # Stop Hardware Alarm
            self.serial_worker.send_command('0')

            if helmet_id in self.helmets_in_alert:
                self.helmets_in_alert.remove(helmet_id)
                self.clear_alert(helmet_id)
                
            self.dashboard_page.co_status_label.setText("NORMAL")
            self.dashboard_page.co_status_label.setStyleSheet("color: #2dd4bf;")

        self.update_all_ui()

    def update_all_ui(self):
        """Distributes data to all child pages."""
        self.data_warehouse_page.update_helmet_list(self.helmet_data, self.current_helmet_id)
        self.fleet_map_page.update_map(self.helmet_data)
        self.analysis_page.update_data(self.helmet_data, self.current_helmet_id)
        
        if self.current_helmet_id and self.helmet_data.get(self.current_helmet_id):
            latest_data = self.helmet_data[self.current_helmet_id][-1]
            self.update_dashboard_display(latest_data)

    def update_dashboard_display(self, data):
        self.helmet_id_label.setText(f"ID: {data.get('helmetId', 'N/A')}")
        page = self.dashboard_page
        
        # Update Dashboard Widgets
        page.co_card.value_label.animate_to_value(data.get('gas', 0))
        page.temp_card.value_label.animate_to_value(data.get('temperature', 0))
        page.humidity_card.value_label.animate_to_value(data.get('humidity', 0))
        page.methane_card.value_label.animate_to_value(data.get('methane', 0))
        page.nat_gas_card.value_label.animate_to_value(data.get('natural_gas', 0))
        
        lat = data.get('latitude', 0.0)
        lng = data.get('longitude', 0.0)
        
        page.main_latitude_label.setText(f"{lat:.6f}" if lat != 0.0 else "No GPS Fix")
        page.main_longitude_label.setText(f"{lng:.6f}" if lng != 0.0 else "No GPS Fix")
        page.battery_card.set_level(data.get('battery', 0))
        
        if lat != 0.0:
            page.map_card.update_marker(lat, lng, data.get('gas', 0), self.co_threshold)
            page.gps_status_label.setStyleSheet("color: #2dd4bf;")
            page.gps_status_label.setText("ACTIVE")
        else:
            page.gps_status_label.setStyleSheet("color: #9E9E9E;")
            page.gps_status_label.setText("NO FIX")

        if self.helmet_data.get(self.current_helmet_id):
            page.graph_canvas.update_plot(self.helmet_data[self.current_helmet_id])

    @Slot(int, int, int)
    def update_thresholds(self, co, meth, lpg):
        print(f"Updating Thresholds -> CO: {co}, CH4: {meth}, LPG: {lpg}")
        self.co_threshold = co
        self.methane_threshold = meth
        self.lpg_threshold = lpg
        # Update visual line on graph
        self.dashboard_page.graph_canvas.set_threshold(self.co_threshold)

    @Slot(str)
    def change_active_helmet(self, helmet_id):
        print(f"Changing active helmet to: {helmet_id}")
        self.current_helmet_id = helmet_id
        self.handle_nav(0, self.nav_btn_dash) # Go to dashboard
        
        if self.helmet_data.get(helmet_id) and self.helmet_data[helmet_id]:
            self.update_dashboard_display(self.helmet_data[helmet_id][-1])

    @Slot()
    def clear_alert(self, helmet_id):
        self.dashboard_page.alert_panel.remove_alert(helmet_id)
        if not self.helmets_in_alert:
            self.dashboard_page.alert_panel.set_alert_state(False)

    # --- UI SETUP ---
    def _setup_ui(self):
        main_widget = QWidget()
        root_layout = QVBoxLayout(main_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.header = self._create_header()
        root_layout.addWidget(self.header)

        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar_container = self._create_sidebar()
        
        # Setup Stacked Pages
        self.stacked_widget = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.data_warehouse_page = DataWarehousePage()
        self.analysis_page = HistoricalAnalysisPage()
        self.fleet_map_page = FleetMapPage()
        self.settings_page = SettingsPage(self.co_threshold, self.methane_threshold, self.lpg_threshold)
        
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.data_warehouse_page)
        self.stacked_widget.addWidget(self.analysis_page)
        self.stacked_widget.addWidget(self.fleet_map_page)
        self.stacked_widget.addWidget(self.settings_page)
        
        # Connect Page Signals
        self.data_warehouse_page.helmet_selected.connect(self.change_active_helmet)
        self.settings_page.thresholds_updated.connect(self.update_thresholds)

        body_layout.addWidget(self.sidebar_container)
        
        # Content Wrapper
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.addWidget(self.stacked_widget)
        
        body_layout.addWidget(content_area, 1)
        root_layout.addWidget(body_widget, 1)
        self.setCentralWidget(main_widget)

    def _create_header(self):
        LOGO_SIZE = 70
        HEADER_HEIGHT = 90
        
        widget = QWidget()
        widget.setObjectName("headerWidget") 
        widget.setFixedHeight(HEADER_HEIGHT) 
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(25, 0, 25, 0)
        layout.setSpacing(20)

        # Logo
        logo_label = QLabel()
        logo_label.setFixedSize(LOGO_SIZE, LOGO_SIZE)
        if os.path.exists("logo.png"):
            pixmap = QPixmap("logo.png")
            scaled = pixmap.scaled(LOGO_SIZE, LOGO_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled)
            logo_label.setStyleSheet("border: none; background: transparent;")
        else:
            # Fallback shield drawing if needed... (omitted for brevity, rely on shared logic if possible or keep it simple)
            logo_label.setText("🛡️")
            logo_label.setStyleSheet("font-size: 40px; border: none; background: transparent;")
            
        layout.addWidget(logo_label)

        # Title & Time
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        title_layout.setAlignment(Qt.AlignVCenter)
        
        self.title_label = QLabel("SHIELDX SMART HELMET")
        self.title_label.setObjectName("headerLabel")
        self.time_label = QLabel("--:--")
        self.time_label.setObjectName("timeLabel")
        self.update_header_time()
        
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.time_label)
        layout.addWidget(title_container)
        layout.addStretch(1) 

        # Status
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setSpacing(20)
        self.helmet_id_label = QLabel("ID: ---")
        self.helmet_id_label.setObjectName("statusHeaderLabel")
        self.connection_status_label = QLabel("CONNECTED")
        self.connection_status_label.setObjectName("statusHeaderLabel")
        self.connection_status_label.setStyleSheet("color: #2dd4bf;")
        status_layout.addWidget(self.helmet_id_label)
        status_layout.addWidget(self.connection_status_label)
        layout.addWidget(status_container)

        # Buttons
        self.pause_button = HoverButton(text="Pause")
        self.pause_button.setFixedWidth(100)
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self.toggle_pause)
        
        save_button = HoverButton(text="Snapshot")
        save_button.setFixedWidth(100)
        save_button.clicked.connect(self.save_snapshot)
        layout.addWidget(self.pause_button)
        layout.addWidget(save_button)
        
        return widget

    def _create_sidebar(self):
        self.sidebar_container = QWidget()
        self.sidebar_container.setObjectName("sidebar")
        self.sidebar_container.setFixedWidth(self.sidebar_collapsed_width)
        layout = QVBoxLayout(self.sidebar_container)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(10)

        self.toggle_btn = QPushButton()
        self.toggle_btn.setIcon(IconFactory.get("menu"))
        self.toggle_btn.setIconSize(self.toggle_btn.sizeHint())
        self.toggle_btn.setObjectName("toggleButton")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setFixedHeight(40)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        layout.addWidget(self.toggle_btn)
        layout.addSpacing(20)

        # Nav Buttons
        self.nav_btn_dash = SidebarButton("dashboard", "Dashboard")
        self.nav_btn_dash.setChecked(True)
        self.nav_btn_dash.clicked.connect(lambda: self.handle_nav(0, self.nav_btn_dash))
        
        self.nav_btn_ware = SidebarButton("warehouse", "Data Warehouse")
        self.nav_btn_ware.clicked.connect(lambda: self.handle_nav(1, self.nav_btn_ware))
        
        self.nav_btn_anal = SidebarButton("analysis", "Analysis")
        self.nav_btn_anal.clicked.connect(lambda: self.handle_nav(2, self.nav_btn_anal))
        
        self.nav_btn_map = SidebarButton("map", "Fleet Map")
        self.nav_btn_map.clicked.connect(lambda: self.handle_nav(3, self.nav_btn_map))
        
        self.nav_btn_sett = SidebarButton("settings", "Settings")
        self.nav_btn_sett.clicked.connect(lambda: self.handle_nav(4, self.nav_btn_sett))

        self.nav_buttons = [self.nav_btn_dash, self.nav_btn_ware, self.nav_btn_anal, self.nav_btn_map, self.nav_btn_sett]
        for btn in self.nav_buttons:
            layout.addWidget(btn)
            
        layout.addStretch(1)
        
        self.pause_btn = SidebarButton("pause", "Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.save_btn = SidebarButton("camera", "Snapshot")
        self.save_btn.clicked.connect(self.save_snapshot)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.save_btn)
        
        self.all_sidebar_btns = self.nav_buttons + [self.pause_btn, self.save_btn]
        for btn in self.all_sidebar_btns:
            btn.update_mode(collapsed=True)
            
        return self.sidebar_container

    def toggle_sidebar(self):
        self.is_sidebar_expanded = not self.is_sidebar_expanded
        start_w = self.sidebar_collapsed_width if self.is_sidebar_expanded else self.sidebar_expanded_width
        end_w = self.sidebar_expanded_width if self.is_sidebar_expanded else self.sidebar_collapsed_width
        
        if not self.is_sidebar_expanded: # Collapsing
            for btn in self.all_sidebar_btns:
                btn.update_mode(collapsed=True)

        self.anim_group = QParallelAnimationGroup()
        anim_min = QPropertyAnimation(self.sidebar_container, b"minimumWidth")
        anim_min.setDuration(250)
        anim_min.setStartValue(start_w)
        anim_min.setEndValue(end_w)
        anim_min.setEasingCurve(QEasingCurve.InOutQuad)
        
        anim_max = QPropertyAnimation(self.sidebar_container, b"maximumWidth")
        anim_max.setDuration(250)
        anim_max.setStartValue(start_w)
        anim_max.setEndValue(end_w)
        anim_max.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.anim_group.addAnimation(anim_min)
        self.anim_group.addAnimation(anim_max)
        self.anim_group.finished.connect(self.on_sidebar_anim_finished)
        self.anim_group.start()

    def on_sidebar_anim_finished(self):
        if self.is_sidebar_expanded:
            for btn in self.all_sidebar_btns:
                btn.update_mode(collapsed=False)
        try:
            self.anim_group.finished.disconnect(self.on_sidebar_anim_finished)
        except:
            pass

    def handle_nav(self, index, active_btn):
        self.stacked_widget.setCurrentIndex(index)
        for btn in self.nav_buttons:
            btn.setChecked(btn is active_btn)

    def update_header_time(self):
        if hasattr(self, 'time_label'):
            self.time_label.setText(datetime.now(tz=None).strftime('%A, %B %d, %Y  |  %I:%M:%S %p'))

    def toggle_pause(self):
        self.serial_worker.is_running = not self.serial_worker.is_running
        new_text = "Resume" if not self.serial_worker.is_running else "Pause"
        self.pause_button.setText(new_text)
        self.pause_btn.setText(new_text)
        
        if self.serial_worker.is_running and not self.serial_worker.isRunning():
            self.serial_worker.start()

    def save_snapshot(self):
        filename = f"snapshot_dark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.grab().save(filename)
        print(f"✅ Screenshot saved to {filename}")

    def closeEvent(self, event):
        self.serial_worker.stop()
        self.weather_worker.stop()
        event.accept()

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', sans-serif; color: #E0E0E0; }
            QMainWindow { background-color: #141414; }
            
            /* SIDEBAR */
            #sidebar { background-color: #09090b; border-right: 1px solid #27272a; }
            #toggleButton { background-color: transparent; color: #FFFFFF; font-size: 18px; border: none; border-radius: 8px; }
            #toggleButton:hover { background-color: #27272a; }
            
            SidebarButton { background-color: transparent; color: #A1A1AA; font-size: 11pt; font-weight: 600; border-radius: 8px; text-align: left; padding-left: 15px; }
            SidebarButton:hover { background-color: rgba(255, 255, 255, 0.08); color: #FFFFFF; }
            SidebarButton:checked { background-color: #1d4ed8; color: #09090b; }
            
            /* HEADER */
            #headerWidget { background-color: #09090b; border-bottom: 1px solid #27272a; }
            #headerLabel { font-size: 18pt; font-weight: 800; color: #FFFFFF; letter-spacing: 1px; }
            #statusHeaderLabel { font-size: 16pt; font-weight: 700; color: #E0E0E0; }
            
            /* CARDS */
            #statusCard, #card { background-color: #1F1F1F; border-radius: 0px; }
            #pTasksCard, #aTasksCard, #humidityCard, #methaneCard, #natGasCard { border-radius: 10px; color: #FFFFFF; }
            
            #pTasksCard { background-color: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #a855f7, stop:1 #ef4444); }
            #aTasksCard { background-color: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #f97316, stop:1 #facc15); }
            #humidityCard { background-color: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #3b82f6, stop:1 #2dd4bf); }
            #methaneCard { background-color: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #65a30d, stop:1 #a3e635); }
            #natGasCard { background-color: qlineargradient(x1:0, y1:1, x2:1, y2:0, stop:0 #db2777, stop:1 #f472b6); }
            
            #dataCardTitle { font-size: 14pt; font-weight: 700; color: rgba(255, 255, 255, 0.9); }
            #dataCardValue { font-size: 32pt; font-weight: 700; color: #FFFFFF; }
            #dataCardUnit { font-size: 13pt; font-weight: 600; color: rgba(255, 255, 255, 0.8); }
            
            #locationInfoCard { background-color: #27272a; border-radius: 4px; } 
            #locationCardSubTitle { font-size: 10pt; font-weight: 600; color: #A1A1AA; } 
            #locationCardValue { font-size: 16pt; font-weight: 700; color: #FFFFFF; }
            
            #cardTitle { font-size: 13pt; font-weight: 700; color: #FFFFFF; text-transform: uppercase;}
            QFormLayout QLabel { font-size: 9pt; color: #9E9E9E; }
            #statusLabel { font-size: 10pt; font-weight: 700; }
            #batteryValue { font-size: 16pt; font-weight: 700; color: #FFFFFF; }
        """)