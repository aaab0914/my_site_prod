import hashlib
import mimetypes
import os
import re
from pathlib import Path
from urllib.parse import quote

from django.http import FileResponse, Http404, HttpResponse, HttpResponseNotModified, StreamingHttpResponse
from django.utils.http import http_date, parse_http_date_safe, quote_etag

_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


def _range_stream(file_obj, start, end, chunk_size=8192):
    file_obj.seek(start)
    remaining = end - start + 1
    while remaining > 0:
        chunk = file_obj.read(min(chunk_size, remaining))
        if not chunk:
            break
        remaining -= len(chunk)
        yield chunk


def _safe_etag(cache_prefix, file_path, last_modified, file_size):
    raw = f"{cache_prefix}:{file_path}:{int(last_modified)}:{file_size}".encode("utf-8", errors="ignore")
    digest = hashlib.sha256(raw).hexdigest()
    return quote_etag(digest)


def _content_disposition(file_path):
    ascii_name = file_path.name.encode("ascii", errors="ignore").decode("ascii") or f"download{file_path.suffix}"
    utf8_name = quote(file_path.name)
    return f'inline; filename="{ascii_name}"; filename*=UTF-8''{utf8_name}'


def serve_protected_media(field_file, request=None, cache_prefix="media"):
    if not field_file:
        raise Http404("File not found.")

    file_path = Path(field_file.path)
    if not file_path.is_file():
        raise Http404("File not found.")

    stat_result = os.stat(file_path)
    last_modified = stat_result.st_mtime
    file_size = stat_result.st_size
    etag = _safe_etag(cache_prefix, file_path, last_modified, file_size)
    content_disposition = _content_disposition(file_path)

    if request is not None:
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match and if_none_match == etag:
            response = HttpResponseNotModified()
        else:
            if_modified_since = parse_http_date_safe(request.headers.get("If-Modified-Since", ""))
            if if_modified_since and int(last_modified) <= if_modified_since:
                response = HttpResponseNotModified()
            else:
                response = None
    else:
        response = None

    content_type, _ = mimetypes.guess_type(file_path.name)
    content_type = content_type or "application/octet-stream"

    if response is None and request is not None:
        range_header = request.headers.get("Range", "").strip()
        match = _RANGE_RE.fullmatch(range_header)
        if match:
            start_raw, end_raw = match.groups()
            if start_raw == "" and end_raw == "":
                return HttpResponse(status=416)

            if start_raw == "":
                length = int(end_raw)
                start = max(file_size - length, 0)
                end = file_size - 1
            else:
                start = int(start_raw)
                end = int(end_raw) if end_raw else file_size - 1

            if start >= file_size or start < 0 or end < start:
                range_response = HttpResponse(status=416)
                range_response["Content-Range"] = f"bytes */{file_size}"
                range_response["Accept-Ranges"] = "bytes"
                return range_response

            end = min(end, file_size - 1)
            length = end - start + 1
            file_handle = open(file_path, "rb")
            response = StreamingHttpResponse(
                _range_stream(file_handle, start, end),
                status=206,
                content_type=content_type,
            )
            response["Content-Length"] = str(length)
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Content-Disposition"] = content_disposition

    if response is None:
        response = FileResponse(open(file_path, "rb"), content_type=content_type)
        response["Content-Disposition"] = content_disposition
        response["Content-Length"] = str(file_size)

    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = "public, max-age=7776000, immutable"
    response["ETag"] = etag
    response["Last-Modified"] = http_date(last_modified)
    return response
