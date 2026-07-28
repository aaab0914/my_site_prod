#!/usr/bin/env python3
"""Counts across content models

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__media_model_counts.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from blog.models import AudioPost, Comment, Post, VideoPost
    from images.models import Album, AlbumImage, ImagePost
    rows = {
        "posts": Post.objects.count(),
        "comments": Comment.objects.count(),
        "audio_posts": AudioPost.objects.count(),
        "video_posts": VideoPost.objects.count(),
        "gallery_images": ImagePost.objects.count(),
        "albums": Album.objects.count(),
        "album_images": AlbumImage.objects.count(),
    }
    print(rows)


if __name__ == "__main__":
    main()
