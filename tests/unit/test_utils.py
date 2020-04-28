# coding: utf-8
import pytest
import os
import filecmp

from PySide2.QtGui import (
    QImage,
)

from PySideLib.QCdtUtils import (
    BatchImageLoader,
    ImageLoadingCallback,
    LruCache,
)


class TestBatchImageLoader(object):

    class _Context(object):
        def __init__(self):
            self.imagePath0 = ''
            self.imagePath1 = ''
            self.imagePathInvalid = ''

    @pytest.fixture()
    def context(self):
        ctx = TestBatchImageLoader._Context()
        resourceDir = os.path.join(os.path.dirname(__file__), 'resources')
        ctx.imagePath0 = os.path.join(resourceDir, 'test_0000.png')
        ctx.imagePath1 = os.path.join(resourceDir, 'test_0001.png')
        ctx.outImagePath0 = os.path.join(resourceDir, 'out_0000.png')
        ctx.outImagePath1 = os.path.join(resourceDir, 'out_0001.png')

        yield ctx

        if os.path.isfile(ctx.outImagePath0):
            os.remove(ctx.outImagePath0)
        if os.path.isfile(ctx.outImagePath1):
            os.remove(ctx.outImagePath1)

    def test_loadAsync(self, context):
        print(context.imagePath0)
        loader = BatchImageLoader()
        task_id0 = loader.addFile(context.imagePath0)
        task_id1 = loader.addFile(context.imagePath1)

        loader.loadAsync().get()

        image0 = loader.image(task_id0)
        image1 = loader.image(task_id1)

        image0.save(context.outImagePath0)
        image1.save(context.outImagePath1)

        assert filecmp.cmp(context.imagePath0, context.outImagePath0, shallow=False)
        assert filecmp.cmp(context.imagePath1, context.outImagePath1, shallow=False)

    def test_callbacks(self, context):
        loader = BatchImageLoader()
        task_id1 = loader.addFile(context.imagePath0)

        def _assert_loaded(img):
            img.save(context.outImagePath0)
            assert filecmp.cmp(context.imagePath0, context.outImagePath0, shallow=False)
            return img

        def _assert_complete():
            assert loader.image(task_id1) is not None

        loader.addCallback(ImageLoadingCallback.LOADED, _assert_loaded)
        loader.addCallback(ImageLoadingCallback.COMPLETED, _assert_complete)

        loader.loadAsync().get()

    # loadAsync()内で起きた例外をPyTestが拾ってしまうのでテストできない
    # def test_errorCallbacks(self, context):
    #     loader = BatchImageLoader()
    #     loader.addFile(1)
    #
    #     def _assert_error(e):
    #         assert isinstance(e, TypeError)
    #
    #     loader.addCallback(ImageLoadingCallback.ERROR, _assert_error)
    #     loader.loadAsync().get()


class TestLruCache(object):

    def test_add(self):
        cache = LruCache(size=3)

        cache.set('key1', 1)
        assert cache.get('key1') == 1

        cache.set('key2', 2)
        assert cache.get('key2') == 2

        cache.set('key3', 3)
        assert cache.get('key3') == 3

    def test_overflow(self):
        cache = LruCache(size=3)
        cache.set('key1', 1)
        cache.set('key2', 2)
        cache.set('key3', 3)
        assert cache.size() == 3

        # add key4, key1 is removed
        cache.set('key4', 4)
        assert cache.size() == 3
        assert cache.get('key1') is None
        assert cache.get('key2') == 2
        assert cache.get('key3') == 3
        assert cache.get('key4') == 4

        # touch key2
        cache.get('key2')
        # add key5, key3 is removed
        cache.set('key5', 5)
        assert cache.get('key3') is None
        assert cache.get('key2') == 2
        assert cache.get('key4') == 4
        assert cache.get('key5') == 5
