"""Clear Redis-cached compiled templates."""

from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clear compiled template cache from Redis."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pattern",
            default="template:",
            help="Cache key pattern to delete (default: 'template:')",
        )

    def handle(self, *args, **options):
        pattern = options["pattern"]
        try:
            deleted = cache.delete_pattern(f"{pattern}*")
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {deleted} keys matching '{pattern}*'")
            )
        except AttributeError:
            # 如果 cache 后端不支持 delete_pattern，fallback
            self.stdout.write(
                self.style.WARNING(
                    "Cache backend does not support delete_pattern; "
                    "consider flushing all."
                )
            )