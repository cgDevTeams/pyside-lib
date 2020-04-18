from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout
)


class TestQTabWidget:
    """
    Group of tests for QTabWidget
    """

    def test_addWidget(self, qtbot, sample_list_str):
        from PySideLib.QCdtWidgets import QTagWidget
        tagWidget = QTagWidget(qtbot, sample_list_str)
        qtbot.addWidget(tagWidget)
