from contextvars import ContextVar


_current_request = ContextVar("current_request", default=None)


def set_current_request(request):
    return _current_request.set(request)


def reset_current_request(token):
    _current_request.reset(token)


def get_current_request():
    return _current_request.get()


def is_browser_delete_request():
    request = get_current_request()
    if request is None:
        return False
    return request.method in {"POST", "DELETE"}
