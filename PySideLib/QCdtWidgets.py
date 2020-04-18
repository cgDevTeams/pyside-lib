"""
"""
import sys
from functools import partial

from typing import (
    NewType,
    NoReturn,
    List,
)

from PySide2.QtCore import (
    Qt,
    QObject,
    QModelIndex,
    QAbstractListModel,
    QStringListModel,
    QAbstractProxyModel,
    QSortFilterProxyModel,
    QPoint,
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
        self.setWrapping(True)
        self.setResizeMode(QListView.Adjust)
        self.setViewMode(QListView.IconMode)


class QImageFlowModelItem(object):

    def __init__(self):
        self.__image = None  # type: QImage

    def setImage(self, image):
        # type: (QImage) -> NoReturn
        self.__image = image

    def image(self):
        # type: () -> QImage
        return self.__image


TImageFlowModelItem = NewType('TImageFlowModelItem', QImageFlowModelItem)


class QImageFlowModel(QAbstractListModel):

    ItemRole = Qt.UserRole + 1
    UserRole = ItemRole + 1

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QImageFlowModel, self).__init__(parent)
        self.__items = []  # type: List[TImageFlowModelItem]

    def append(self, item):
        # type: (TImageFlowModelItem) -> NoReturn
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + 1)
        self.__items.append(item)
        self.endInsertRows()

    def extend(self, items):
        # type: (List[TImageFlowModelItem]) -> NoReturn
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + len(items))
        self.__items.extend(items)
        self.endInsertRows()

    def remove(self, item):
        # type: (TImageFlowModelItem) -> NoReturn
        index = self.__items.index(item)
        self.beginRemoveRows(QModelIndex(), index, index + 1)
        self.__items.remove(item)
        self.endRemoveRows()

    def reset(self, items):
        # type: (List[TImageFlowModelItem]) -> NoReturn
        self.beginResetModel()
        self.__items = items
        self.endResetModel()

    def clear(self):
        # type: () -> NoReturn
        self.reset([])

    def item(self, index):
        # type: (QModelIndex) -> TImageFlowModelItem
        return self.__items[index.row()]

    def rowCount(self, parent=QModelIndex()):
        # type: (QModelIndex) -> int
        return len(self.__items)

    def data(self, index, role=Qt.DisplayRole):
        # type: (QModelIndex, int) -> object
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self.__items):
            return None

        item = self.item(index)

        if role == Qt.DecorationRole:
            return item.image()

        if role == QImageFlowModel.ItemRole:
            return item

        return None


TImageFlowView = NewType('TImageFlowView', QImageFlowView)
TImageFlowModel = NewType('TImageFlowModel', QImageFlowModel)


class QImageFlowDirection(object):

    LeftToRight = QListView.LeftToRight
    TopToBottom = QListView.TopToBottom


class QImageFlowWidget(QWidget):

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QImageFlowWidget, self).__init__(parent)
        model = self.modelType()(self)

        self.__view = self.viewType()(self)
        self.__view.setModel(model)

        self.__scrollArea = QScrollArea()
        self.__scrollArea.setWidgetResizable(True)
        self.__scrollArea.setWidget(self.__view)

        mainLayout = QHBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.addWidget(self.__scrollArea)
        self.setLayout(mainLayout)

        self.__flowDirection = self.setFlowDirection(QImageFlowDirection.LeftToRight)

    def viewType(self):
        # type: () -> type
        return QImageFlowView

    def modelType(self):
        # type: () -> type
        return QImageFlowModel

    def setFlowDirection(self, direction):
        # type: (str) -> str
        if direction == QImageFlowDirection.LeftToRight:
            self.view().setFlow(direction)
            self.__scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.__scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            return direction

        if direction == QImageFlowDirection.TopToBottom:
            self.view().setFlow(direction)
            self.__scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.__scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            return direction

    def flowDirection(self):
        # type: () -> str
        return self.__flowDirection

    def setProxyModel(self, proxy):
        # type: (QAbstractProxyModel) -> NoReturn
        model = self.model()
        if isinstance(model, QAbstractProxyModel):
            proxy.setSourceModel(model.sourceModel())
            model.deleteLater()
        else:
            proxy.setSourceModel(model)
        self.view().setModel(proxy)

    def view(self):
        # type: () -> TImageFlowView
        return self.__view

    def model(self):
        # type: () -> TImageFlowModel
        return self.view().model()

    def appendItem(self, item):
        # type: (TImageFlowModelItem) -> NoReturn
        model = self.model()
        if isinstance(model, QAbstractProxyModel):
            model = model.sourceModel()
        model.append(item)

    def appendImage(self, image):
        # type: (QImage) -> NoReturn
        item = QImageFlowModelItem()
        item.setImage(image)
        self.appendItem(item)

    def appendFile(self, filePath):
        # type: (str) -> NoReturn
        image = QImage(filePath)
        self.appendImage(image)


if __name__ == '__main__':
    import sys, glob, random, os
    from PySide2.QtCore import QSize, QRegExp
    from PySide2.QtWidgets import QApplication, QMainWindow, QScrollArea

    app = QApplication()
    window = QMainWindow()
    window.setMinimumSize(QSize(640, 480))

    class _FlowItem(QImageFlowModelItem):
        def __init__(self, filePath):
            super(_FlowItem, self).__init__()
            self.filePath = filePath
            self.name = os.path.basename(filePath)

        def __repr__(self):
            return "{}('{}')".format(self.__class__.__name__, self.filePath)

    class _FlowView(QImageFlowView):
        def mouseDoubleClickEvent(self, event):
            index = self.indexAt(event.pos())
            proxy = self.model()
            index = proxy.mapToSource(index)
            item = proxy.sourceModel().item(index)
            print(index, item)

    class _FlowModel(QImageFlowModel):
        FileNameRole = QImageFlowModel.UserRole + 1

        def data(self, index, role=Qt.DisplayRole):
            if role == _FlowModel.FileNameRole:
                return self.item(index).name
            if role == Qt.DisplayRole:
                return self.item(index).name
            return super(_FlowModel, self).data(index, role)

    class _FlowWidget(QImageFlowWidget):
        def viewType(self):
            return _FlowView

        def modelType(self):
            return _FlowModel

    imageFlow = _FlowWidget(window)

    proxy = QSortFilterProxyModel()
    proxy.setFilterRole(_FlowModel.FileNameRole)
    imageFlow.setProxyModel(proxy)

    def setFilter(text):
        proxy.setFilterWildcard(text)

    searchFilter = QLineEdit()
    # searchFilter.textChanged.connect(lambda text: proxy.setFilterWildcard(text))
    searchFilter.textChanged.connect(setFilter)

    w = QWidget()
    l = QVBoxLayout()
    l.addWidget(searchFilter)
    l.addWidget(imageFlow)
    w.setLayout(l)
    window.setCentralWidget(w)
    window.show()

    for i, filePath in enumerate(glob.glob('C:/tmp/test_images2/*.png')):
        image = QImage(filePath).scaled(100 + random.randint(0, 100), 100 + random.randint(0, 100))
        item = _FlowItem(filePath)
        item.setImage(image)
        imageFlow.appendItem(item)

    sys.exit(app.exec_())
