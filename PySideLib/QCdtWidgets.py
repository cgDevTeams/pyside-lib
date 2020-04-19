"""
"""
import os
import pathlib
from functools import partial

from typing import (
    TypeVar,
    NoReturn,
    Optional,
    Any,
    List,
    Union,
)

from PySide2.QtCore import (
    Qt,
    QObject,
    QModelIndex,
    QAbstractListModel,
    QStringListModel,
    QAbstractItemModel,
    QAbstractProxyModel,
    QSortFilterProxyModel,
    QRect,
    QPoint,
    QSize,
    Signal,
    QItemSelection,
)

from PySide2.QtWidgets import (
    QWidget,
    QFrame,
    QLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QSizePolicy,
    QCompleter,
    QListView,
    QScrollArea,
    QTreeView,
    QAbstractItemView,
)

from PySide2.QtGui import (
    QImage,
    QStandardItem,
    QStandardItemModel,
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


# https://github.com/pyside/Examples/blob/master/examples/layouts/flowlayout.py
class QFlowLayout(QLayout):

    def __init__(self, parent=None, margin=0, spacing=-1):
        super(QFlowLayout, self).__init__(parent)

        if parent is not None:
            self.setMargin(margin)

        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(QFlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()


TListItem = TypeVar('TListItem')


class QListModel(QAbstractListModel):

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QListModel, self).__init__(parent)
        self.__items = []  # type: List[TListItem]

    def append(self, item):
        # type: (TListItem) -> NoReturn
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + 1)
        self.__items.append(item)
        self.endInsertRows()

    def extend(self, items):
        # type: (List[TListItem]) -> NoReturn
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + len(items))
        self.__items.extend(items)
        self.endInsertRows()

    def remove(self, item):
        # type: (TListItem) -> NoReturn
        index = self.__items.index(item)
        self.beginRemoveRows(QModelIndex(), index, index + 1)
        self.__items.remove(item)
        self.endRemoveRows()

    def reset(self, items):
        # type: (List[TListItem]) -> NoReturn
        self.beginResetModel()
        self.__items = items.copy()
        self.endResetModel()

    def clear(self):
        # type: () -> NoReturn
        self.reset([])

    def item(self, index):
        # type: (Union[int, QModelIndex]) -> TListItem
        if isinstance(index, QModelIndex):
            index = index.row()
        if isinstance(index, int):
            return self.__items[index]
        raise RuntimeError('the type of "index" must be QModelIndex or int')

    def items(self):
        # type: () -> List[TListItem]
        return self.__items

    def rowCount(self, parent=QModelIndex()):
        # type: (QModelIndex) -> int
        return len(self.__items)


class QFlowView(QListView):

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QFlowView, self).__init__(parent)
        self.setWrapping(True)
        self.setResizeMode(QListView.Adjust)
        self.setViewMode(QListView.IconMode)


class QFlowDirection(object):

    LeftToRight = 'LeftToRight'
    TopToBottom = 'TopToBottom'


class QImageFlowModelItem(object):

    def __init__(self):
        self.__image = None  # type: QImage

    def setImage(self, image):
        # type: (QImage) -> NoReturn
        self.__image = image

    def image(self):
        # type: () -> QImage
        return self.__image


class QImageFlowView(QFlowView):

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QImageFlowView, self).__init__(parent)
        self.setViewMode(QListView.IconMode)


class QImageFlowModel(QListModel):

    def data(self, index, role=Qt.DisplayRole):
        # type: (QModelIndex, int) -> Any
        if role != Qt.DecorationRole:
            return None
        if not index.isValid() or not 0 <= index.row() < self.rowCount():
            return None

        return self.item(index).image()


class _ViewModelWidgetBase(QWidget):

    def __init__(self, parent, defaultViewType, defaultModelType):
        # type: (QObject, type, type) -> NoReturn
        super(_ViewModelWidgetBase, self).__init__(parent)
        self.__defaultViewType = defaultViewType
        self.__defaultModelType = defaultModelType
        self._view = self.viewType()(self)  # type: QAbstractItemView
        self._view.setModel(self.modelType()(self))

    def viewType(self):
        # type: () -> type
        return self.__defaultViewType

    def modelType(self):
        # type: () -> type
        return self.__defaultModelType

    def view(self):
        # type: () -> QAbstractItemView
        return self._view

    def model(self):
        # type: () -> QAbstractItemModel
        return self.view().model()

    def _sourceModel(self):
        # type: () -> QAbstractItemModel()
        model = self.model()
        if isinstance(model, QAbstractProxyModel):
            model = model.sourceModel()
        return model


TImageFlowView = TypeVar('TImageFlowView', bound=QImageFlowView)
TImageFlowModel = TypeVar('TImageFlowModel', bound=QImageFlowModel)


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

        self.__flowDirection = self.setFlowDirection(QFlowDirection.LeftToRight)

    def viewType(self):
        # type: () -> type
        return QImageFlowView

    def modelType(self):
        # type: () -> type
        return QListModel

    def setFlowDirection(self, direction):
        # type: (str) -> str
        if direction == QFlowDirection.LeftToRight:
            self.view().setFlow(QListView.LeftToRight)
            self.__scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.__scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            return direction

        if direction == QFlowDirection.TopToBottom:
            self.view().setFlow(QListView.TopToBottom)
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
        # type: (TImageFlowModelItem) -> TImageFlowModelItem
        model = self.model()
        if isinstance(model, QAbstractProxyModel):
            model = model.sourceModel()
        model.append(item)
        return item

    def appendImage(self, image):
        # type: (QImage) -> TImageFlowModelItem
        item = QImageFlowModelItem()
        item.setImage(image)
        return self.appendItem(item)

    def appendFile(self, filePath):
        # type: (str) -> TImageFlowModelItem
        image = QImage(filePath)
        return self.appendImage(image)


class QDirectoryTreeItem(QStandardItem):

    def __init__(self, path):
        # type: (Union[str, pathlib.Path]) -> NoReturn
        super(QDirectoryTreeItem, self).__init__()
        if isinstance(path, str):
            self.__path = pathlib.Path(path)
        else:
            self.__path = path

        if self.hasChild():
            self.appendRow(None)

        self.setEditable(False)

    def path(self):
        # type: () -> pathlib.Path
        return self.__path

    def name(self):
        # type: () -> str
        path = self.path()
        if len(path.name) > 0:
            return path.name
        return path.drive

    def hasChild(self):
        # type: () -> bool
        for child in self.path().glob('*'):
            if child.is_dir():
                return True
        return False


TDirectoryTreeItem = TypeVar('TDirectoryTreeItem', bound=QDirectoryTreeItem)


class QDirectoryTreeView(QTreeView):

    itemSelectionChanged = Signal((QItemSelection, QItemSelection))

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QDirectoryTreeView, self).__init__(parent)
        self.expanded.connect(self.__on_item_expanded)

    def selectionChanged(self, selected, deselected):
        # type: (QItemSelection, QItemSelection) -> NoReturn
        self.itemSelectionChanged.emit(selected, deselected)

    def __on_item_expanded(self, index):
        # type: (QModelIndex) -> NoReturn
        model = self.model()
        if model is None:
            return
        model.expand(index)


class QDirectoryTreeModel(QStandardItemModel):

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QDirectoryTreeModel, self).__init__(parent)

    def setRootDirectoryPaths(self, paths):
        # type: (List[Union[str, pathlib.Path]]) -> NoReturn
        item = self.invisibleRootItem()
        item.removeRows(0, item.rowCount())
        item.appendRows([self.createItem(path) for path in paths])

    def headerData(self, section, orientation, role):
        # type: (int, int, int) -> str
        return ''

    def data(self, index, role=Qt.DisplayRole):
        # type: (QModelIndex, int) -> Any
        if role != Qt.DisplayRole:
            return None
        if not index.isValid() or index.row() < 0:
            return None

        item = self.itemFromIndex(index)
        return item.name()

    def createItem(self, path):
        # type: (pathlib.Path) -> TDirectoryTreeItem()
        return QDirectoryTreeItem(path)

    def expand(self, index):
        # type: (QModelIndex) -> NoReturn
        item = self.itemFromIndex(index)
        item.removeRows(0, item.rowCount())
        item.appendRows([self.createItem(path) for path in item.path().glob('*') if path.is_dir()])


TDirectoryTreeView = TypeVar('TDirectoryTreeView', bound=QDirectoryTreeView)
TDirectoryTreeModel = TypeVar('TDirectoryTreeModel', bound=QDirectoryTreeModel)


class QDirectoryTreeWidget(_ViewModelWidgetBase):

    itemSelectionChanged = Signal(QItemSelection, QItemSelection)

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QDirectoryTreeWidget, self).__init__(parent, QDirectoryTreeView, QDirectoryTreeModel)
        self._view.itemSelectionChanged.connect(self.itemSelectionChanged.emit)
        self._view.customContextMenuRequested.connect(self.customContextMenuRequested.emit)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)
        self.setLayout(layout)

    def setSelectionMode(self, mode):
        # type: (int) -> NoReturn
        self._view.setSelectionMode(mode)

    def setContextMenuPolicy(self, policy):
        # type: (ContextMenuPolicy) -> NoReturn
        self._view.setContextMenuPolicy(policy)

    def itemFromIndex(self, index):
        # type: (QModelIndex) -> TDirectoryTreeItem
        model = self.model()
        if isinstance(model, QAbstractProxyModel):
            index = model.mapToSource(index)
            model = model.sourceModel()
        return model.itemFromIndex(index)

    def currentItem(self):
        # type: () -> TDirectoryTreeItem
        index = self.view().currentIndex()
        return self.itemFromIndex(index)

    def selectedItems(self):
        # type: () -> List[TDirectoryTreeItem]
        return [self.itemFromIndex(index) for index in self._view.selectedIndexes()]

    def setRootDirectoryPaths(self, paths):
        # type: (List[Union[str, pathlib.Path]]) -> NoReturn
        self._sourceModel().setRootDirectoryPaths(paths)
