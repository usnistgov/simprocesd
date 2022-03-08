from unittest.mock import patch, MagicMock


def add_side_effect_to_class_method(test_case, target, original_method = None, side_effect = None):
    ''' Configure side_effect and original_method to be called with parameters
    that the target is normally called with. For target format see target
    parameter used by unittest.mock.patch

    Returns mock object for the target.
    '''
    # Configure patch target.
    patcher = patch(target, autospec = True)
    # Add patcher cleanup
    test_case.addCleanup(patcher.stop)
    # Start the patch and get the mock.
    target_mock = patcher.start()

    # Add helper method to be called when target is called, helper will
    # in turn call the callback and the original method.
    def _help(*args, original_method = original_method, side_effect = side_effect, **kwargs):
        if side_effect is not None:
            side_effect(*args, **kwargs)
        if original_method is not None:
            return original_method(*args, **kwargs)

    if original_method is not None or side_effect is not None:
        target_mock.side_effect = _help
    return target_mock


def mock_wrap(object_):
    ''' Returns MagicMock object that wraps object_ and has
    specifications set to that of object_. If object_ is iterable then a
    list of MagicMock items is returned where each object_ item is
    wrapped individually.
    '''
    wrap = lambda obj_: MagicMock(spec = obj_, wraps = obj_)
    if hasattr(object_ , '__iter__'):
        rtn = []
        for o in object_:
            rtn.append(wrap(o))
        return rtn
    else:
        return wrap(object_)

