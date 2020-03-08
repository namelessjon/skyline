import datetime
from contextlib import contextmanager
import functools
import time

from .event import _timer_name
from .threadlocal_client import ThreadLocalClient
from .version import __version__


_SKL = None


def init(dataset='', debug=False):
    global _SKL

    if _SKL is None:
        _SKL = ThreadLocalClient(dataset=dataset, debug=debug)
    else:
        print("Library already initialized: client=%s new_dataset=%r" % (_SKL, dataset))


def add_context(data):
    '''Similar to add_context_field(), but allows you to add a number of name:value pairs
    to the currently active event at the same time.
    `skyline.add_context({ "first_field": "a", "second_field": "b"})`
    Args:
    - `data`: dictionary of field names (strings) to field values to add
    '''
    if _SKL and _SKL._event:
        _SKL.add_context(data=data)

def add_context_field(name, value):
    ''' Add a field to the currently active event. For example, if you are
    using django and wish to add additional context to the current request
    before it is sent:
    `skyline.add_context_field("my field", "my value")`
    Args:
    - `name`: Name of field to add
    - `value`: Value of new field
    '''
    if _SKL and _SKL._event:
        _SKL.add_context_field(name=name, value=value)

def remove_context_field(name):
    ''' Remove a single field from the current span.
    ```
    skyline.add_context({ "first_field": "a", "second_field": "b"})
    skyline.remove_context_field("second_field")
    Args:
    - `name`: Name of field to remove
    ```
     '''

    if _SKL and _SKL._event:
        _SKL.remove_context_field(name=name)

def add_rollup_field(name, value):
    ''' AddRollupField adds a key/value pair to the current event. If it is called repeatedly
    on the same event, the values will be summed together.
    Args:
    - `name`: Name of field to add
    - `value`: Numeric (float) value of new field
    '''

    if _SKL and _SKL._event:
        _SKL.add_rollup_field(name=name, value=value)

@contextmanager
def timer(name):
    """ Timer yields block (think `with` statement) and counts the time
     taken during that block.  The time is added to the event.  If there
     are multiple invocations with the same name, these will be added up
     over the whole event.
    It is especially useful for doing things like adding the duration spent talking
    to a specific external service - eg database time
    """
    if _SKL and _SKL._event:
        with _SKL._event.add_timer_field(name):
            yield
    else:
        yield


def done():
    ''' close the skyline client, flushing any unsent events. '''
    global _SKL
    if _SKL:
        _SKL.done()

    _SKL = None

def evented():
    """Decorator for wrapping a generic function in an event.
    
    The event will be sent when the function ends, possibly annotated with
    any exception raised."""
    def wrapped(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            if _SKL:
                with _SKL.evented():
                    return fn(*args, **kwargs)
            else:
                return fn(*args, **kwargs)

        return inner

    return wrapped


def _log(message, *args):
    if _SKL and _SKL.debug:
        print(message % args)