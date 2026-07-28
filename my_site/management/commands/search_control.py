from django.conf import settings
from django.core.cache import cache
from django.core.management import BaseCommand, call_command

from elasticsearch import Elasticsearch

from blog.documents import PostDocument
from blog.models import Post
from blog.search import elasticsearch_is_available, es_search_result_ids, invalidate_search_caches


class Command(BaseCommand):
    help = "Control center for Elasticsearch status, rebuild, and sample queries."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["status", "rebuild", "sample", "clear-cache", "sync-post"])
        parser.add_argument("--query", default="python")
        parser.add_argument("--post-id", type=int)

    def handle(self, *args, **options):
        action = options["action"]
        if action == "status":
            self.print_status()
            return
        if action == "rebuild":
            call_command("search_index", "--rebuild", "-f")
            invalidate_search_caches()
            cache.clear()
            self.stdout.write(self.style.SUCCESS("Elasticsearch index rebuilt and caches cleared."))
            self.print_status()
            return
        if action == "sample":
            query = options["query"]
            result_ids = es_search_result_ids(query)
            self.stdout.write(f"sample query: {query}")
            self.stdout.write(f"result ids: {result_ids[:20]}")
            return
        if action == "clear-cache":
            invalidate_search_caches()
            cache.clear()
            self.stdout.write(self.style.SUCCESS("Search caches cleared."))
            return
        if action == "sync-post":
            post_id = options.get("post_id")
            if not post_id:
                raise SystemExit("--post-id is required for sync-post")
            post = Post.objects.get(pk=post_id)
            PostDocument().update(post)
            invalidate_search_caches()
            self.stdout.write(self.style.SUCCESS(f"Post {post_id} synced to Elasticsearch."))
            return

    def print_status(self):
        hosts = settings.ELASTICSEARCH_DSL["default"]["hosts"]
        client = Elasticsearch(hosts)
        ping = client.ping()
        exists = client.indices.exists(index="posts") if ping else False
        count = client.count(index="posts")["count"] if exists else 0
        cluster = client.cluster.health(index="posts") if exists else {}
        self.stdout.write(f"ping: {ping}")
        self.stdout.write(f"available helper: {elasticsearch_is_available(force=True)}")
        self.stdout.write(f"index exists: {exists}")
        self.stdout.write(f"document count: {count}")
        if cluster:
            self.stdout.write(f"health: {cluster.get('status')}")
