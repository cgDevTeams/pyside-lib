# coding: utf-8
import threading
import multiprocessing.pool

from typing import (
    NoReturn,
    Optional,
    Callable,
    Any,
    List,
    Dict,
    Tuple,
)

from PySide2.QtCore import (
    QObject,
    Signal,
    QEvent,
    QCoreApplication,
)

from PySide2.QtGui import (
    QImage,
)


class _MethodInvokeEvent(QEvent):

    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, func, args, kwargs):
        # type: (Callable[[Any], Any], Any, Any) -> NoReturn
        super(_MethodInvokeEvent, self).__init__(_MethodInvokeEvent.EVENT_TYPE)
        self.func = func
        self.args = args
        self.kwargs = kwargs


class _MethodInvoker(QObject):

    def __init__(self):
        super(_MethodInvoker, self).__init__()

    def event(self, e):
        # type: (_MethodInvokeEvent) -> bool
        e.func(*e.args, **e.kwargs)
        return True


class Dispatcher(QObject):

    invoker = _MethodInvoker()

    @staticmethod
    def begin_invoke(func, *args, **kwargs):
        # type: (Callable[[Any], Any], Any, Any) -> NoReturn
        QCoreApplication.postEvent(Dispatcher.invoker, _MethodInvokeEvent(func, args, kwargs))


class ImageLoadingCallback(object):

    ERROR = 'ERROR'
    LOADED = 'LOADED'
    COMPLETED = 'COMPLETED'


class BatchImageLoader(QObject):

    loaded = Signal(int)
    completed = Signal()

    def __init__(self, parent=None):
        # type: (QObject) -> NoReturn
        super(BatchImageLoader, self).__init__(parent)
        self.__filePaths = {}  # type: Dict[int, str]
        self.__images = {}  # type: Dict[int, Optional[QImage]]
        self.__imagesLock = threading.Lock()
        self.__callbacks = {}  # type: Dict[str, List[Callable[[QImage], QImage]]]
        self.__pool = multiprocessing.pool.ThreadPool()

    def addFile(self, file_path):
        # type: (str) -> int
        index = len(self.__filePaths) + 1
        self.__filePaths[index] = file_path
        self.__images[index] = None
        return index

    def addCallback(self, callback_id, callback):
        # type: (str, Callable[[QImage], QImage]) -> None
        callbacks = self.__callbacks.get(callback_id, [])
        callbacks.append(callback)
        self.__callbacks[callback_id] = callbacks

    def image(self, task_id):
        # type: (int) -> Optional[QImage]
        return self.__images.get(task_id)

    def loadAsync(self):
        # type: () -> multiprocessing.pool.AsyncResult
        errorCallbacks = self.__callbacks.get(ImageLoadingCallback.ERROR, [])
        loadedCallbacks = self.__callbacks.get(ImageLoadingCallback.LOADED, [])
        completedCallbacks = self.__callbacks.get(ImageLoadingCallback.COMPLETED, [])

        def _taskCallback(_args):
            # type: (Tuple[int, str]) -> NoReturn
            _index, _filePath = _args
            self.__loadImage(_index, _filePath, loadedCallbacks)

        def _callback(_):
            for on_completed in completedCallbacks:
                on_completed()
            self.completed.emit()

        def _errorCallback(e):
            for callback in errorCallbacks:
                callback(e)

        return self.__pool.map_async(
            _taskCallback,
            self.__filePaths.items(),
            callback=_callback,
            error_callback=_errorCallback
        )

    def __loadImage(self, index, file_path, onLoadedCallbacks):
        # type: (int, str, List[Callable[[QImage], QImage]]) -> None
        image = QImage(file_path)
        with self.__imagesLock:
            self.__images[index] = image

        newImage = image
        for on_loaded in onLoadedCallbacks:
            newImage = on_loaded(newImage)

        if newImage != image:
            with self.__imagesLock:
                self.__images[index] = newImage

        self.loaded.emit(index)
