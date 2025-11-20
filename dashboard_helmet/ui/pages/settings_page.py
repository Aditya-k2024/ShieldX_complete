from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QLineEdit, QMessageBox
)
from PySide6.QtCore import Signal
from ui.components.shared import HoverButton

class SettingsPage(QWidget):
    # Signal now sends 3 integers: CO, Methane, LPG
    thresholds_updated = Signal(int, int, int)

    def __init__(self, co_val, methane_val, lpg_val, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        
        layout = QFormLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("⚠️ Safety Threshold Configuration")
        title.setObjectName("headerLabel")
        layout.addRow(title)
        
        desc = QLabel("Set the raw sensor levels or PPM values that trigger an alarm.")
        desc.setStyleSheet("color: #9E9E9E; font-size: 10pt; margin-bottom: 10px;")
        layout.addRow(desc)

        # 1. CO Input
        self.co_input = QLineEdit(str(co_val))
        self.co_input.setStyleSheet("font-size: 12pt; padding: 8px; background: #333; border: 1px solid #444; color: white; border-radius: 4px;")
        layout.addRow("CO Limit (Toxic):", self.co_input)

        # 2. Methane Input
        self.meth_input = QLineEdit(str(methane_val))
        self.meth_input.setStyleSheet("font-size: 12pt; padding: 8px; background: #333; border: 1px solid #444; color: white; border-radius: 4px;")
        layout.addRow("Methane Limit (CH4):", self.meth_input)

        # 3. LPG Input
        self.lpg_input = QLineEdit(str(lpg_val))
        self.lpg_input.setStyleSheet("font-size: 12pt; padding: 8px; background: #333; border: 1px solid #444; color: white; border-radius: 4px;")
        layout.addRow("LPG/Nat. Gas Limit:", self.lpg_input)

        layout.addRow(QLabel("")) # Spacer

        # Apply Button
        self.apply_button = HoverButton(text="Save Configuration")
        self.apply_button.setFixedWidth(200)
        self.apply_button.clicked.connect(self._apply_changes)
        layout.addRow(self.apply_button)

    def _apply_changes(self):
        try:
            new_co = int(self.co_input.text())
            new_meth = int(self.meth_input.text())
            new_lpg = int(self.lpg_input.text())
            
            # Emit all three values
            self.thresholds_updated.emit(new_co, new_meth, new_lpg)
            
            QMessageBox.information(self, "Success", "Safety thresholds updated successfully!")
            print(f"New Thresholds -> CO: {new_co}, CH4: {new_meth}, LPG: {new_lpg}")
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid whole numbers (integers) for all fields.")