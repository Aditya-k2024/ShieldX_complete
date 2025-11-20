from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, Slot
from datetime import datetime

# --- HISTORICAL ALERT LOG (Internal Component) ---
class HistoricalAlertLog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("📜 ALERT HISTORY (ALL EVENTS)")
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        
        self.log_list = QListWidget()
        self.log_list.setStyleSheet("""
            QListWidget { 
                background-color: #27272a; 
                border-radius: 12px; 
                padding: 5px;
            }
            QListWidget::item { 
                border-bottom: 1px solid #444; 
                padding: 5px;
            }
        """)
        layout.addWidget(self.log_list, 1)
        
    @Slot(dict)
    def add_alert(self, data):
        helmet_id = data.get('helmetId')
        gas_level = data.get('gas', 0)
        timestamp = datetime.now().strftime("%I:%M:%S %p")
        
        item = QListWidgetItem()
        item_text = f"""
        <div style='padding: 4px;'>
            <span style='font-size: 9pt; color: #9E9E9E;'>{timestamp}</span><br>
            <span style='font-size: 11pt; color: #ef4444; font-weight: bold;'>{helmet_id}</span>
            <span style='font-size: 11pt; color: #E0E0E0;'> - CO Level: {gas_level:.0f} ppm</span>
        </div>
        """
        label = QLabel(item_text)
        label.setWordWrap(True)
        item.setSizeHint(label.sizeHint())
        self.log_list.insertItem(0, item)
        self.log_list.setItemWidget(item, label)


# --- MAIN WAREHOUSE PAGE ---
class DataWarehousePage(QWidget):
    helmet_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setSpacing(20)
        
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0,0,0,0)
        
        title = QLabel("Connected Helmets")
        title.setObjectName("headerLabel")
        
        self.helmet_list = QListWidget()
        self.helmet_list.setStyleSheet("""
            QListWidget { background-color: #1F1F1F; border-radius: 16px; font-size: 12pt; padding: 5px; } 
            QListWidget::item { padding: 10px; border-bottom: 1px solid #333333; } 
            QListWidget::item:hover { background-color: #333333; } 
            QListWidget::item:selected { background-color: #1d4ed8; color: white; }
        """)
        self.helmet_list.itemClicked.connect(self._on_item_clicked)
        
        list_layout.addWidget(title)
        list_layout.addWidget(self.helmet_list, 1)
        
        self.historical_log = HistoricalAlertLog()
        
        self.main_layout.addWidget(list_container, 2)
        self.main_layout.addWidget(self.historical_log, 1)

    def update_helmet_list(self, helmet_data, active_helmet_id):
        self.helmet_list.blockSignals(True)
        self.helmet_list.clear()
        for helmet_id, data_packets in sorted(helmet_data.items()):
            if not data_packets:
                continue
            last_packet = data_packets[-1]
            last_seen = last_packet['timestamp']
            last_co = last_packet['gas']
            
            item_text = f"<b>ID: {helmet_id}</b><br><span style='font-size: 10pt; color: #9E9E9E;'>Last Seen: {last_seen} | Last CO: {last_co:.0f} ppm</span>"
            list_item = QListWidgetItem()
            list_item.setData(Qt.UserRole, helmet_id)
            self.helmet_list.addItem(list_item)
            
            label = QLabel(item_text)
            label.setWordWrap(True)
            list_item.setSizeHint(label.sizeHint())
            self.helmet_list.setItemWidget(list_item, label)
            
            if helmet_id == active_helmet_id:
                self.helmet_list.setCurrentItem(list_item)
        self.helmet_list.blockSignals(False)

    @Slot(QListWidgetItem)
    def _on_item_clicked(self, item):
        if item:
            helmet_id = item.data(Qt.UserRole)
            self.helmet_selected.emit(helmet_id)