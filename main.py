import sys
from PyQt6.QtWidgets import QApplication
from core.main_window import MarkdownConverterGUI

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MarkdownConverterGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()