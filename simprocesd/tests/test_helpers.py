from unittest.mock import patch, MagicMock


def add_side_effect_to_class_method(test_case, target, replacement = None, side_effect = None):
    ''' Configure side_effect and replacement to be called with
    parameters that the target is normally called with.

    Arguments:
    test_case - TestCase whose cleanup will be used to cleanup the
        patch.
    target - For target format see target parameter used by
        unittest.mock.patch
    replacement - method to replace the original call. If None
        (default) then the original call will remain.
    side_effect - an additional function to be called when the call
        to the target is made.

    Return: a mock object for the target.
    '''
    # Configure patch target.
    patcher = patch(target, autospec = True)
    # Add patcher cleanup
    test_case.addCleanup(patcher.stop)
    # Start the patch and get the mock.
    target_mock = patcher.start()

    # Add helper method to be called when target is called, helper will
    # in turn call the callback and the original method.
    def _help(*args, replacement = replacement, side_effect = side_effect, **kwargs):
        if side_effect is not None:
            side_effect(*args, **kwargs)
        if replacement is not None:
            return replacement(*args, **kwargs)

    if replacement is not None or side_effect is not None:
        target_mock.side_effect = _help
    return target_mock


def mock_wrap(object_):
    ''' Returns MagicMock object that wraps object_ and has
    specifications set to that of object_. If object_ is iterable then a
    list of MagicMock items is returned where each object_ item is
    wrapped individually.
    '''
    wrap = lambda item: MagicMock(spec = item, wraps = item)
    if hasattr(object_ , '__iter__'):
        rtn = []
        for o in object_:
            rtn.append(wrap(o))
        return rtn
    else:
        return wrap(object_)

