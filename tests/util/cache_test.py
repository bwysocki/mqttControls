from __future__ import absolute_import

from mock import Mock, create_autospec

from octoprint_mqtt_controls.util import cached_property, cached_call


def test_cached_property():
    expected_value = 42

    mock_method = Mock(return_value=expected_value)

    class TestedClass(object):
        @cached_property
        def mocked_property(self):
            return mock_method(self)

    instance = TestedClass()
    print(dir(instance))

    retrieved_value = None
    for _ in range(2):
        retrieved_value = instance.mocked_property

    mock_method.assert_called_once_with(instance)
    assert retrieved_value == expected_value


def test_cached_call():
    expected_value = 42

    mock = Mock(return_value=expected_value)
    mock.__name__ = 'mocked_function'

    decorated = cached_call(mock)

    retrieved_value = None
    for _ in range(2):
        retrieved_value = decorated()

    mock.assert_called_once()
    assert retrieved_value == expected_value
