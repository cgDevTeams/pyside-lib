# coding: utf-8
import sys
import os
import glob

from PySide2.QtCore import (
    Qt,
    QSize,
    QSortFilterProxyModel,
)

from PySide2.QtGui import (
    QImage,
)

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLineEdit,
    QVBoxLayout,
    QMessageBox,
    QSizePolicy,
    QHBoxLayout,
)

from PySideLib.QCdtWidgets import (
    QDirectoryTreeItem,
    QDirectoryTreeModel,
    QDirectoryTreeView,
    QDirectoryTreeWidget,
)

from PySideLib.QCdtUtils import (
    BatchImageLoader,
    ImageLoadingCallback,
)


def main():
    app = QApplication()
    window = QMainWindow()
    window.setMinimumSize(600, 600)

    w = QDirectoryTreeWidget(window)
    w.setRootDirectoryPaths(['C:\\', 'D:\\'])
    w.itemClicked.connect(lambda item: print(item.path()))

    window.setCentralWidget(w)
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
