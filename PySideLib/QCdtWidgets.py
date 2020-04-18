"""
"""
import sys
from functools import partial

from typing import (
    NoReturn,
    List,
)

from PySide2.QtCore import (
    Qt,
    QObject,
    QModelIndex,
    QStringListModel,
    QAbstractListModel,
    QSortFilterProxyModel,
)

from PySide2.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QSizePolicy,
    QCompleter,
    QListView,
)

from PySide2.QtGui import (
    QImage,
)


class QTagWidget(QWidget):

    def __init__(self, parent, items):
        super(QTagWidget, self).__init__()
        self.parent = parent
        self.items = items

        self.tags = []
        self.mainFrame = QFrame()
        self.mainFrame.setStyleSheet(
            'border:1px solid #76797C; border-radius: 1px;')

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.mainFrame)

        self.hLayout = QHBoxLayout()
        self.hLayout.setSpacing(4)

        self.lineEdit = QLineEdit()
        self.lineEdit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        completer = QPartialMatchCompleter(self.lineEdit)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.lineEdit.setCompleter(completer)

        model = QStringListModel()
        completer.setModel(model)
        model.setStringList(self.items)

        self.mainFrame.setLayout(self.hLayout)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.hLayout.setContentsMargins(2, 2, 2, 2)

        self.refresh()

        self.setup_ui()

    def show(self):
        self.show()

    def setup_ui(self):
        self.lineEdit.returnPressed.connect(self.create_tags)

    def create_tags(self):
        new_tags = self.lineEdit.text().split(', ')
        self.lineEdit.setText('')
        self.tags.extend(new_tags)
        self.tags = list(set(self.tags))
        self.tags.sort(key=lambda x: x.lower())
        self.refresh()

    def refresh(self):
        for i in reversed(range(self.hLayout.count())):
            self.hLayout.itemAt(i).widget().setParent(None)
        for tag in self.tags:
            self.add_tag_to_bar(tag)
        self.hLayout.addWidget(self.lineEdit)
        self.lineEdit.setFocus()

        # Accept to add only 5 tags
        if len(self.tags) >= 5:
            self.lineEdit.setDisabled(True)
            return

    def add_tag_to_bar(self, text):
        tag = QFrame()
        tag.setStyleSheet(
            'border:1px solid rgb(192, 192, 192); border-radius: 4px;')
        tag.setContentsMargins(2, 2, 2, 2)
        tag.setFixedHeight(28)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(4, 4, 4, 4)
        hbox.setSpacing(10)

        tag.setLayout(hbox)

        label = QLabel(text)
        label.setStyleSheet('border:0px')
        label.setFixedHeight(16)
        hbox.addWidget(label)

        x_button = QPushButton('x')
        x_button.setFixedSize(20, 20)
        x_button.setStyleSheet('border:0px; font-weight:bold')
        x_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        x_button.clicked.connect(partial(self.delete_tag, text))
        hbox.addWidget(x_button)

        tag.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        self.hLayout.addWidget(tag)

    def delete_tag(self, tag_name):
        self.tags.remove(tag_name)

        # Make input available if tags count is less than 5
        if len(self.tags) < 5:
            self.lineEdit.setDisabled(False)
        self.refresh()


class QPartialMatchCompleter(QCompleter):

    def __init__(self, parent):
        super(QPartialMatchCompleter, self).__init__(parent)

        self.local_completion_prefix = ""
        self.source_model = None

    def setModel(self, model):
        self.source_model = model
        super(QPartialMatchCompleter, self).setModel(self.source_model)

    def updateModel(self):
        local_completion_prefix = self.local_completion_prefix

        class InnerProxyModel(QSortFilterProxyModel):
            def filterAcceptsRow(self, sourceRow, sourceParent):
                index0 = self.sourceModel().index(sourceRow, 0, sourceParent)
                return local_completion_prefix.lower() in self.sourceModel().data(index0).lower()

        proxyModel = InnerProxyModel()
        proxyModel.setSourceModel(self.source_model)
        super(QPartialMatchCompleter, self).setModel(proxyModel)

    def splitPath(self, path):
        self.local_completion_prefix = path
        self.updateModel()
        return ""


class QImageFlowView(QListView):

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QImageFlowView, self).__init__(parent)
        self.setFlow(QListView.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListView.Adjust)

    def mouseDoubleClickEvent(self, e):
        # type: (QMouseEvent) -> NoReturn
        index = self.indexAt(e.pos())
        index = self.__proxy_model.mapToSource(index)
        item = self.__proxy_model.sourceModel().data(index, Qt.ItemDataRole)
        if item is not None:
            print(item.path)


class QImageFlowModel(QAbstractListModel):

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QImageFlowModel, self).__init__(parent)
        self.__items = []  # type: List[QImage]

    def append(self, item):
        # type: (QImage) -> NoReturn
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + 1)
        self.__items.append(item)
        self.endInsertRows()

    def extend(self, items):
        # type: (List[QImage]) -> NoReturn
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + len(items))
        self.__items.extend(items)
        self.endInsertRows()

    def clear(self):
        # type: () -> NoReturn
        self.__items = []

    def rowCount(self, parent=QModelIndex()):
        # type: (QModelIndex) -> int
        return len(self.__items)

    def data(self, index, role=Qt.DisplayRole):
        # type: (QModelIndex, Qt.ItemDataRole) -> object
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self.__items):
            return None

        if role == Qt.DecorationRole:
            return self.__items[index.row()]

        return None


class QImageFlowWidget(QWidget):

    @property
    def model(self):
        # type: () -> QImageFlowModel
        return self.proxyModel.sourceModel()

    @property
    def proxyModel(self):
        # type: () -> QSortFilterProxyModel
        return self.__view.model()

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QImageFlowWidget, self).__init__(parent)
        self.__view = QImageFlowView(self)
        self.__view.setViewMode(QListView.IconMode)

        model = QImageFlowModel(self)
        proxy = QSortFilterProxyModel(self)
        proxy.setSourceModel(model)
        self.__view.setModel(proxy)

        layout = QHBoxLayout()
        layout.addWidget(self.__view)
        self.setLayout(layout)

    def appendImage(self, image):
        # type: (QImage) -> NoReturn
        self.model.append(image)


import sys, glob
from PySide2.QtWidgets import QApplication, QMainWindow, QScrollArea

app = QApplication()
window = QMainWindow()

area = QScrollArea()
area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
area.setWidgetResizable(True)

imageFlow = QImageFlowWidget(area)
for filePath in glob.glob('C:/tmp/test_images2/*.png'):
    image = QImage(filePath).scaled(100, 100)
    imageFlow.appendImage(image)

area.setWidget(imageFlow)
window.setCentralWidget(area)
window.show()

sys.exit(app.exec_())
