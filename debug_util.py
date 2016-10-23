

__depth = 0
def trace(func):
    def wrapper(*args, **kwargs):
        global __depth
        print '  ' * __depth, func, args, kwargs
        old_depth = __depth
        __depth = __depth + 1
        v = func(*args, **kwargs)
        __depth = old_depth
        print '  ' * __depth, '=>', v
        return v
    return wrapper

