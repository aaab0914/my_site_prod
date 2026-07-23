def request_query_string(request, updates=None, *, remove=None):
    query = request.GET.copy()
    for key in remove or []:
        query.pop(key, None)
    for key, value in (updates or {}).items():
        if value in (None, ""):
            query.pop(key, None)
        else:
            query[key] = value
    encoded = query.urlencode()
    return f"?{encoded}" if encoded else ""


def build_sort_context(request, sort_options, *, default_sort, page_param="page", sort_param="sort"):
    selected_sort = request.GET.get(sort_param, default_sort)
    if selected_sort not in sort_options:
        selected_sort = default_sort

    return {
        "selected_sort": selected_sort,
        "sort_options": [
            {
                "value": value,
                "label": label,
                "active": value == selected_sort,
                "url": request_query_string(
                    request,
                    updates={sort_param: value},
                    remove=[page_param],
                ),
            }
            for value, label in sort_options.items()
        ],
        "pagination_suffix": request_query_string(
            request,
            updates={sort_param: selected_sort},
            remove=[page_param],
        ),
    }
