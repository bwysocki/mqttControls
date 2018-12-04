from __future__ import absolute_import

from itertools import ifilter

from .job_state import JobStateCommand
from .printer_state import PrinterStateCommand

commands = (
    JobStateCommand,
    PrinterStateCommand,
)


def get_command(command_name):
    try:
        result = next(
            ifilter(lambda c: c.COMMAND_NAME == command_name, commands)
        )
    except StopIteration:
        raise ValueError('No command found')

    return result
