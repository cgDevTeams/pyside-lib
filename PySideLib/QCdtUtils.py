# coding: utf-8
import sys
import threading
import multiprocessing.pool
import pathlib
import cProfile
import pstats
import io
import collections
import functools
import contextlib

from typing import (
    TypeVar,
    Generic,
    NoReturn,
    Optional,
    Callable,
    Iterable,
    Any,
    List,
    Dict,
    Tuple,
    Union,
)

from PySide2.QtCore import (
    QObject,
    Signal,
    QEvent,
    QCoreApplication,
    QMimeDatabase,
    QFileInfo,
)

from PySide2.QtGui import (
    QImage,
    QIcon,
)

from PySide2.QtWidgets import (
    QFileIconProvider,
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


TCacheKey = TypeVar('TCacheKey')
TCacheValue = TypeVar('TCacheValue')


class LruCache(Generic[TCacheKey, TCacheValue]):

    def __init__(self, size):
        # type: (int) -> NoReturn
        self.__size = 0
        self.__itemsDic = collections.OrderedDict()
        self.resize(size)

    def __getitem__(self, item):
        # type: (TCacheKey) -> Any
        return self.__itemsDic[item]

    def __setitem__(self, key, value):
        # type: (TCacheKey, TCacheValue) -> NoReturn
        self.set(key, value)

    def size(self):
        # type: () -> int
        return self.__size

    def resize(self, size):
        # type: (int) -> NoReturn
        self.__size = size
        self.__itemsDic.clear()

    def get(self, key, defaultValue=None):
        # type: (TCacheKey, TCacheValue) -> TCacheValue
        item = self.__itemsDic.get(key)
        if item is None:
            return defaultValue

        self.__itemsDic.move_to_end(key)
        return item

    def set(self, key, value):
        # type: (TCacheKey, TCacheValue) -> Optional[TCacheValue]
        if key in self.__itemsDic:
            self.__itemsDic[key] = value
            self.__itemsDic.move_to_end(key)
            return None

        removed = self.__itemsDic.popitem(last=False) if len(self.__itemsDic) >= self.size() else None
        self.__itemsDic[key] = value
        return removed


@contextlib.contextmanager
def profileCtx(sortKey=pstats.SortKey.CUMULATIVE, stream=sys.stdout):
    # type: (str, io.TextIOBase) -> NoReturn
    profiler = cProfile.Profile()
    profiler.enable()
    yield
    profiler.disable()
    stat = pstats.Stats(profiler, stream=stream).sort_stats(sortKey)
    stat.print_stats()


def profile(sortKey=pstats.SortKey.CUMULATIVE, stream=sys.stdout):
    # type: (str, io.TextIOBase) -> Callable
    def _deco(func):
        @functools.wraps(func)
        def _with_profile(*args, **kwargs):
            with profileCtx(sortKey, stream):
                return func(*args, **kwargs)
        return _with_profile
    return _deco


class QFileIconLoader(QObject):

    class LoadResult(object):

        def __init__(self, filePath, icon):
            # type: (pathlib.Path, QIcon) -> NoReturn
            self.filePath = filePath
            self.icon = icon

    loaded = Signal(LoadResult)
    completed = Signal(dict)

    def __init__(self, parent, cacheSize=1024):
        # type: (QObject, int) -> NoReturn
        super(QFileIconLoader, self).__init__(parent)
        self.__targetPaths = []  # type: List[pathlib.Path]
        self.__iconsCache = LruCache(cacheSize)  # type: LruCache[pathlib.Path, QIcon]
        self.__pool = multiprocessing.pool.ThreadPool(processes=1)
        self.completed.connect(self.reset)

    def append(self, filePath):
        # type: (Union[str, pathlib.Path]) -> NoReturn
        if isinstance(filePath, str):
            filePath = pathlib.Path(filePath)
        self.__targetPaths.append(filePath)

    def extend(self, filePaths):
        # type: (Iterable[Union[str, pathlib.Path]]) -> NoReturn
        for filePath in filePaths:
            self.append(filePath)

    def reset(self, filePaths=[]):
        # type: (Iterable[Union[str, pathlib.Path]]) -> NoReturn
        self.__targetPaths.clear()
        self.extend(filePaths)

    def loadAsync(self, useCache=True):
        # type: (bool) -> multiprocessing.pool.AsyncResult
        targetPaths = self.__targetPaths.copy()

        loadedItems = {}  # type: Dict[pathlib.path, QFileIconLoader.LoadResult]

        if useCache:
            for path in self.__targetPaths:
                icon = self.__iconsCache.get(path)
                if icon is None:
                    continue
                targetPaths.remove(path)
                result = QFileIconLoader.LoadResult(path, icon)
                loadedItems[path] = result
                self.loaded.emit(result)

        itemsLock = threading.Lock()

        def _load(filePath):
            # type: (pathlib.Path) -> NoReturn
            with itemsLock:
                icon = self.__iconsCache.get(filePath)

            if icon is None:
                iconProvider = QFileIconProvider()

                posixPath = filePath.as_posix()
                file = QFileInfo(posixPath)
                icon = iconProvider.icon(file)

                if icon.isNull():
                    mimeDb = QMimeDatabase()
                    for mime in mimeDb.mimeTypesForFileName(posixPath):
                        icon = QIcon.fromTheme(mime.iconName())
                        if not icon.isNull():
                            break

            result = QFileIconLoader.LoadResult(filePath, icon)
            with itemsLock:
                loadedItems[filePath] = result
                self.__iconsCache.set(filePath, icon)

            self.loaded.emit(result)

            if len(loadedItems) == len(targetPaths):
                self.completed.emit(loadedItems)

        return self.__pool.map_async(
            _load,
            targetPaths,
        )
