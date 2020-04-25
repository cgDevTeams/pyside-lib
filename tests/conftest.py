import os
import sys
import pytest

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow
)

# Set path to parent directory
sys.path.add(os.path.abspath(
    os.path.dirname(os.path.abspath(__file__)) + "/../"))

# @pytest.fixture
# def base_window():
#     """Create Base QMainWindow to test as adding layouts and widgets
#     """
#     app = QApplication()
#     mainWindow = QMainWindow()
#     mainWindow.show()
#     return mainWindow


@pytest.fixture
def sample_list_str():
    """Yeild fuilds stirng list: ['apple', 'grape', 'peach', 'strawberry', 'banana']
    """
    yield ['apple', 'grape', 'peach', 'strawberry', 'banana']


@pytest.fixture
def sample_list_number():
    """Yeild fuilds number list: [1, 2, 3, 4, 5]
    """
    yield [1, 2, 3, 4, 5]
