import os
import sys
sys.path.append(os.path.abspath(
    os.path.dirname(os.path.abspath(__file__)) + "/../"))

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
)

from PySideLib.QCdtWidgets import (
    QTagWidget,
)

def main():
    app = QApplication()
    window = QMainWindow()
    tagWidget = QTagWidget()
    window.setCentralWidget(tagWidget)
    window.show()
    sys.exit(app.exec_())



if __name__ == "__main__":
    main()