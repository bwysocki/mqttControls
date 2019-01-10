from __future__ import absolute_import

from mock import Mock

from octoprint_mqtt_controls import cached_property


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
