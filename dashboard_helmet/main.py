import sys
import os
from PySide6.QtWidgets import QApplication

# Ensure the root folder is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import DashboardWindow
from utils import generate_sample_csv

if __name__ == "__main__":
    # Optional: Generate sample data if you want to test the CSV export logic
    # generate_sample_csv() 
    
    app = QApplication(sys.argv)
    
    window = DashboardWindow()
    window.show()
    
    sys.exit(app.exec())