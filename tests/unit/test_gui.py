from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout
)


class TestQTabWidget:
    """
    Group of tests for QTabWidget
    """

    def test_addWidget(self, sample_list_str):
        from PySideLib.QCdtWidgets import QTagWidget
        app = QApplication()
        mainwWindow = QMainWindow()
        tagWidget = QTagWidget(mainwWindow, sample_list_str)
        mainwWindow.setCentralWidget(tagWidget)
        mainwWindow.show()
