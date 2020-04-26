# coding: utf-8
import os
import sys
import threading
import multiprocessing.pool
import subprocess
import tempfile
import json
import shutil
import glob
import pathlib
import datetime
import heapq
import cProfile
import pstats
import io
import collections
import functools

from typing import (
    NoReturn,
    Optional,
    Callable,
    Iterable,
    Any,
    List,
    Dict,
    Tuple,
    Union,
    Set,
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
    QPixmap,
)

from PySide2.QtWidgets import (
    QFileIconProvider,
    QApplication,
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


class LruCache(object):

    def __init__(self, size):
        # type: (int) -> NoReturn
        self.__size = 0
        self.__itemsDic = collections.OrderedDict()
        self.resize(size)

    def __getitem__(self, item):
        # type: (Any) -> Any
        return self.__itemsDic[item]

    def __setitem__(self, key, value):
        # type: (Any, Any) -> NoReturn
        self.set(key, value)

    def size(self):
        # type: () -> int
        return self.__size

    def resize(self, size):
        # type: (int) -> NoReturn
        self.__size = size
        self.__itemsDic.clear()

    def get(self, key, defaultValue=None):
        # type: (Any, Any) -> Any
        item = self.__itemsDic.get(key)
        if item is None:
            return defaultValue

        self.__itemsDic.move_to_end(key)
        return item

    def set(self, key, value):
        # type: (Any, Any) -> Optional[Any]
        if key in self.__itemsDic:
            self.__itemsDic[key] = value
            self.__itemsDic.move_to_end(key)
            return None

        removed = self.__itemsDic.pop(0) if len(self.__itemsDic) >= self.size() else None
        self.__itemsDic[key] = value
        return removed


class Scope(object):

    def _enter(self):
        raise NotImplementedError()

    def _exit(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError()

    def __enter__(self):
        self._enter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._exit(exc_type, exc_val, exc_tb):
            return True
        return False


class ProfileScope(Scope):

    def __init__(self, sortKey=pstats.SortKey.CUMULATIVE, stream=sys.stdout):
        # type: (str, io.TextIOBase) -> NoReturn
        self.__profile = cProfile.Profile()
        self.__sortKey = sortKey
        self.__stream = stream

    def _enter(self):
        self.__profile.enable()

    def _exit(self, exc_type, exc_val, exc_tb):
        self.__profile.disable()
        stat = pstats.Stats(self.__profile, stream=self.__stream).sort_stats(self.__sortKey)
        stat.print_stats()


def profile_scope(func):
    @functools.wraps(func)
    def _with_profile(*args, **kwargs):
        with ProfileScope():
            func(*args, **kwargs)
    return _with_profile


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
        self.__iconsCache = LruCache(cacheSize)
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

    def load_async(self, useCache=True):
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
            icon = self.__iconsCache.get(filePath)
            if icon is None:
                posixPath = filePath.as_posix()
                file = QFileInfo(posixPath)
                icon = QFileIconProvider().icon(file)

                if icon.isNull():
                    mimeDb = QMimeDatabase()
                    for mime in mimeDb.mimeTypesForFileName(posixPath):
                        icon = QIcon.fromTheme(mime.iconName())
                        if not icon.isNull():
                            break

            self.__iconsCache.set(filePath, icon)

            result = QFileIconLoader.LoadResult(filePath, icon)

            with itemsLock:
                loadedItems[filePath] = result

            self.loaded.emit(result)

            if len(loadedItems) == len(targetPaths):
                self.completed.emit(loadedItems)

        return self.__pool.map_async(
            _load,
            targetPaths,
        )
