

__trace_depth = 0


def trace(func):
    def wrapper(*args, **kwargs):
        global __trace_depth
        print '  ' * __trace_depth, func, args, kwargs
        old_depth = __trace_depth
        __trace_depth = __trace_depth + 1
        try:
            v = func(*args, **kwargs)
        finally:
            __trace_depth = old_depth
        print '  ' * __trace_depth, '=>', v
        return v
    return wrapper
