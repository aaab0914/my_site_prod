from django.core.exceptions import PermissionDenied
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from blog.models import AuditLog

from .request_context import is_browser_delete_request
from .runtime_file_guards import ensure_runtime_file_not_protected, is_protected_runtime_path


def enforce_browser_delete_only(label):
    if is_browser_delete_request():
        return
    raise PermissionDenied(f"{label} deletion is only allowed from a browser-triggered request.")


@receiver(pre_delete, sender=AuditLog)
def block_script_audit_log_delete(sender, instance, **kwargs):
    enforce_browser_delete_only("Audit log")


__all__ = [
    "enforce_browser_delete_only",
    "ensure_runtime_file_not_protected",
    "is_protected_runtime_path",
]
