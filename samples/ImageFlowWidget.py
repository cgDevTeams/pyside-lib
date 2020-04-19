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
)

from PySideLib.QCdtWidgets import (
    QImageFlowWidget,
    QImageFlowModel,
    QImageFlowView,
    QImageFlowModelItem,
)

from PySideLib.QCdtUtils import (
    BatchImageLoader,
    ImageLoadingCallback,
)


class FlowItem(QImageFlowModelItem):
    def __init__(self, filePath, image=None):
        super(FlowItem, self).__init__()
        self.filePath = filePath
        self.name = os.path.basename(filePath)
        self.setImage(image)

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.filePath)


class FlowView(QImageFlowView):
    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        proxy = self.model()
        index = proxy.mapToSource(index)
        item = proxy.sourceModel().itemFromIndex(index)
        QMessageBox.information(None, 'test', item.filePath)


class FlowModel(QImageFlowModel):
    FileNameRole = Qt.UserRole + 1

    def data(self, index, role=Qt.DisplayRole):
        if role == FlowModel.FileNameRole:
            return self.itemFromIndex(index).name
        if role == Qt.DisplayRole:
            return self.itemFromIndex(index).name
        return super(FlowModel, self).data(index, role)


class FlowWidget(QImageFlowWidget):
    def viewType(self):
        return FlowView

    def modelType(self):
        return FlowModel


def main():
    app = QApplication()
    window = QMainWindow()
    window.setMinimumSize(QSize(640, 480))

    imageFlow = FlowWidget(window)

    proxy = QSortFilterProxyModel()
    proxy.setFilterRole(FlowModel.FileNameRole)
    proxy.setSortRole(FlowModel.FileNameRole)
    imageFlow.setProxyModel(proxy)

    searchFilter = QLineEdit()
    searchFilter.textChanged.connect(lambda text: proxy.setFilterWildcard(text))

    layout = QVBoxLayout()
    layout.addWidget(searchFilter)
    layout.addWidget(imageFlow)

    widget = QWidget()
    widget.setLayout(layout)

    window.setCentralWidget(widget)
    window.show()

    # 画像を同期読み込み
    # for i, filePath in enumerate(glob.glob('C:/tmp/test_images2/*.png')):
    #     image = QImage(filePath).scaled(100, 100)
    #     item = FlowItem(filePath)
    #     item.setImage(image)
    #     imageFlow.appendItem(item)

    # 画像を非同期読み込み
    loader = BatchImageLoader()
    loader.addCallback(ImageLoadingCallback.LOADED, lambda img: img.scaled(100, 100))
    tasks = {}

    def _on_load_image(taskId):
        filePath = tasks[taskId]
        image = loader.image(taskId)
        item = FlowItem(filePath, image)
        imageFlow.appendItem(item)

    def _on_load_complete():
        proxy.sort(0)

    loader.loaded.connect(_on_load_image)
    loader.completed.connect(_on_load_complete)
    for filePath in glob.iglob('C:/tmp/test_images/*.png'):
        taskId = loader.addFile(filePath)
        tasks[taskId] = filePath

    loader.loadAsync()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
