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
)

from PySide2.QtCore import (
    QObject,
    Signal,
    QEvent,
    QCoreApplication,
)

from PySide2.QtGui import (
    QImage,
    QIcon,
    QPixmap,
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


def getFileIcons(filePaths, by_extention=True):
    # type: (List[Union[str, pathlib.Path]], bool) -> Dict[str, QImage]
    if os.name == 'nt':
        platform = 'win10-x64'
    else:
        # TODO: Mac/Linux対応
        raise NotImplementedError('update submodule "IconExtractor" and build for your platform!')

    executerPath = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'tools', 'IconExtractor', 'build', platform, 'IconExtractor.exe'))

    outputPath = pathlib.Path(os.path.join(tempfile.gettempdir(), '_icon_tmp'))
    if outputPath.is_dir():
        shutil.rmtree(outputPath.as_posix())
    os.makedirs(outputPath.as_posix())

    filePaths = [path.as_posix() if isinstance(path, pathlib.Path) else path for path in filePaths]
    args = {
        'input': filePaths,
        'output': outputPath.as_posix(),
        'by-extension': by_extention,
    }

    argsFilePath = os.path.join(tempfile.gettempdir(), '_create_icons_args.txt')
    with open(argsFilePath, 'w') as f:
        f.write(json.dumps(args))

    try:
        proc = subprocess.Popen(
            [executerPath, '--file', argsFilePath],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except Exception as e:
        # TODO: エラーハンドリング
        print(e)
        return {}

    stdout, stderr = proc.communicate()
    if len(stderr) > 0:
        # TODO: エラーハンドリング
        if platform == 'win10-x64':
            print(stderr.decode('shift-jis'))
        else:
            print(stderr.decode(sys.getdefaultencoding()))
        return {}

    icons = {}  # type: Dict[str, QIcon]
    for iconFilePath in glob.iglob(os.path.join(outputPath, '.*.png')):
        ext = os.path.basename(iconFilePath)[:-len('.png')]
        icons[ext] = QImage(iconFilePath)

    outputs = {}  # type: Dict[str, QIcon]
    for filePath in filePaths:
        _, ext = os.path.splitext(filePath)
        outputs[filePath] = icons.get(ext)

    shutil.rmtree(outputPath)

    return outputs


class QFileIconLoader(QObject):

    loaded = Signal(QIcon)
    completed = Signal()

    def __init__(self, parent):
        # type: (QObject) -> NoReturn
        super(QFileIconLoader, self).__init__(parent)
        self.__paths = []  # type: List[pathlib.Path]
        self.__icons = {}  # type: Dict[pathlib.Path, QIcon]
        self.__pool = multiprocessing.pool.ThreadPool(processes=1)
        self.completed.connect(self.reset)

    def append(self, filePath):
        # type: (Union[str, pathlib.Path]) -> NoReturn
        if isinstance(filePath, str):
            filePath = pathlib.Path(filePath)
        self.__paths.append(filePath)

    def extend(self, filePaths):
        # type: (Iterable[Union[str, pathlib.Path]]) -> NoReturn
        for filePath in filePaths:
            self.append(filePath)

    def reset(self, filePaths=[]):
        # type: (Iterable[Union[str, pathlib.Path]]) -> NoReturn
        self.__paths.clear()
        self.extend(filePaths)

    def icon(self, filePath):
        # type: (Union[str, pathlib.Path]) -> Optional[QIcon]
        if isinstance(filePath, str):
            filePath = pathlib.Path(filePath)
        if filePath.is_dir():
            return None
        return self.__icons.get(filePath.suffix)

    def load_async(self, useCache=True):
        # type: (bool) -> multiprocessing.pool.AsyncResult
        paths = []  # type: List[pathlib.Path]

        # ファイルアイコンを持つのは非ディレクトリだけ
        for path in self.__paths:
            if not path.is_dir():
                paths.append(path)

        if useCache:
            for path in self.__paths:
                icon = self.__icons.get(path.suffix)
                if icon is not None:
                    paths.remove(path)
                    self.loaded.emit(icon)

        # BatchImageLoaderとのI/F統一のためAsyncResultを返したいから1スレッドだけのプールを生成する
        def _load(paths):
            # ファイルアイコンは拡張子単位で変動する
            for filePath, iconImage in getFileIcons(paths, by_extention=True).items():
                icon = QIcon(QPixmap.fromImage(iconImage))
                _, ext = os.path.splitext(filePath)
                self.__icons[ext] = icon
                self.loaded.emit(icon)
                print(f'load: {ext}')
            self.completed.emit()

        return self.__pool.map_async(
            _load,
            [[path.as_posix() for path in paths]],
        )
