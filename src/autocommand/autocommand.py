# Copyright 2014-2015 Nathan West
#
# This file is part of autocommand.
#
# autocommand is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# autocommand is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with autocommand.  If not, see <http://www.gnu.org/licenses/>.

from .autoparse import autoparse
from .automain import automain


def autocommand(
        module, *,
        description=None,
        epilog=None,
        add_nos=False,
        parser=None,
        loop=None,
        forever=False):

    if callable(module):
        raise TypeError('autocommand requires a module name argument')

    def autocommand_decorator(func):
        # Step 1: if requested, run it all in an asyncio event loop
        if loop is not None:
            from asyncio import get_event_loop
            from .autoasync import autoasync

            func = autoasync(
                func,
                loop=get_event_loop() if loop is True else loop,
                forever=forever)

        # Step 2: create parser. We do this second so that the arguments are
        # parsed and passed *before* entering the asyncio event loop. This
        # simplifies the stack trace and ensures errors are reported earlier.
        # It also ensures that errors raised during parsing & passing are still
        # raised if `forever` is True.
        func = autoparse(
            func,
            description=description,
            epilog=epilog,
            add_nos=add_nos,
            parser=parser)

        # Step 3: call the function automatically if __name__ == '__main__' (or
        # if True was provided)
        func = automain(module)(func)

        return func

    return autocommand_decorator
