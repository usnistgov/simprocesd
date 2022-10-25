from unittest import TestCase
import unittest
from unittest.mock import MagicMock, mock_open

from .. import add_side_effect_to_class_method
from ...utils import save_object, load_object


class UtilsTestCase(TestCase):

    def setup_save_load_mocks(self):
        self.file_path = 'test_file.save'
        self.file_exists_path = 'test_file_exists.save'
        self.path_mock = add_side_effect_to_class_method(self, 'os.path.isfile',
                 lambda path: path == self.file_exists_path)

        def open_helper(path, open_flags):
            open_mock = MagicMock()
            open_mock.__enter__.return_value = path
            open_mock.__exit__.return_value = False
            return open_mock

        self.open_mock = add_side_effect_to_class_method(self, 'lzma.open', open_helper)

        self.dump_mock = add_side_effect_to_class_method(self, 'dill.dump')
        self.dump_mock.side_effect = [None]  # Disable any behavior.

        self.test_obj = MagicMock()
        self.load_mock = add_side_effect_to_class_method(self, 'dill.load',
                                                         lambda path: self.test_obj)

    def test_save_object_file_exists(self):
        self.setup_save_load_mocks()

        self.assertRaises(FileExistsError, lambda: save_object(self.test_obj, self.file_exists_path))
        self.path_mock.assert_called_once_with(self.file_exists_path)

    def test_save_object_ignore_exists(self):
        self.setup_save_load_mocks()

        save_object(self.test_obj, self.file_exists_path, True)

        self.path_mock.assert_not_called()
        self.open_mock.assert_called_once_with(self.file_exists_path, 'wb')
        self.dump_mock.assert_called_once_with(self.test_obj, self.file_exists_path)

    def test_save_object(self):
        self.setup_save_load_mocks()

        save_object(self.test_obj, self.file_path)

        self.path_mock.assert_called_once_with(self.file_path)
        self.open_mock.assert_called_once_with(self.file_path, 'wb')
        self.dump_mock.assert_called_once_with(self.test_obj, self.file_path)

    def test_load_object(self):
        self.setup_save_load_mocks()

        self.assertEqual(load_object(self.file_path), self.test_obj)
        self.open_mock.assert_called_once_with(self.file_path, 'rb')
        self.load_mock.assert_called_once_with(self.file_path)


if __name__ == '__main__':
    unittest.main()
