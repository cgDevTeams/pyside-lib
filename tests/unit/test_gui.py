from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout
)

class TestQTabWidget:
    """
    Group of tests for QTabWidget
    """
    def test_addWidget(self, base_window, sample_list_str):
        from PySideLib.QCdtWidgets import QTagWidget
        tagWidget = QTagWidget(base_window, sample_list_str)
        base_window.setCentralWidget(tagWidget)
        # assert hasattr(mainWindow, 'tagWidget')