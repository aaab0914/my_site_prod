from pathlib import Path
import sys

from django.core.management import execute_from_command_line


def main():
    base_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(base_dir))

    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

    import django
    django.setup()

    from my_site.media_cleanup import authorized_media_delete, move_media_file_to_trash

    if len(sys.argv) != 2:
        print("Usage: python scripts/authorized_media_delete.py <relative_media_path>")
        raise SystemExit(1)

    relative_name = sys.argv[1].replace('\\', '/').strip('/')
    with authorized_media_delete():
        result = move_media_file_to_trash(relative_name)
    print(result or "NO_ACTION")


if __name__ == "__main__":
    main()
