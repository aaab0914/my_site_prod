# tests.py
# ========================================
# Imports
# ========================================

from django.test import TestCase, Client
# TestCase: Base class for writing Django unit tests
# Client: Simulated HTTP client for testing views

from django.urls import reverse
# reverse: Function for generating URLs by resolving view names

from django.contrib.auth.models import User
# User: The built-in user model

from django.utils import timezone
# timezone: Utility for handling timezone-aware datetime operations

from django.contrib.admin.sites import AdminSite
# AdminSite: The Django admin site class

from django.contrib.messages import get_messages
# get_messages: Function for retrieving messages from the request

from .models import Post, Comment, AudioPost
# Post: The main blog post model
# Comment: The comment model

from .forms import CommentForm, SearchForm
# CommentForm: Form for adding a comment
# SearchForm: Form for searching posts

from .admin import PostAdmin
# PostAdmin: Admin configuration for the Post model

from .feeds import LatestPostsFeed
# LatestPostsFeed: RSS feed class for the blog

from taggit.models import Tag
# Tag: Model class representing tags

import os
# os: Operating system interface for file and directory operations

from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

import subprocess
# subprocess: Module for running external commands

import unittest
# unittest: Python's built-in unit testing framework
from rest_framework.test import APIClient


# ========================================
# Test Cases
# ========================================

class TagTest(TestCase):
    """
    Test case for tag creation, addition, and querying.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post with Tags',
            slug='test-post-with-tags',
            body='This is a test post with tags.',
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )

    def test_add_tag_to_post(self):
        """Test adding tags to a post."""
        self.post.tags.add('django', 'python', 'testing')
        self.assertEqual(self.post.tags.count(), 3)
        self.assertTrue(self.post.tags.filter(name='django').exists())

    def test_query_posts_by_tag(self):
        """Test querying posts by tag."""
        self.post.tags.add('django', 'python')
        tag = Tag.objects.get(name='django')
        posts = Post.published.filter(tags__in=[tag])
        self.assertEqual(posts.count(), 1)
        self.assertEqual(posts.first().title, 'Test Post with Tags')

    def test_tag_slug_generation(self):
        """Test automatic slug generation for tags."""
        tag = Tag.objects.create(name='Django REST Framework')
        self.assertEqual(tag.slug, 'django-rest-framework')


class RSSFeedTest(TestCase):
    """
    Test case for the RSS feed functionality.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        for i in range(5):
            Post.objects.create(
                title=f'RSS Test Post {i}',
                slug=f'rss-test-post-{i}',
                body=f'This is RSS test post {i} body.',
                author=self.user,
                status=Post.Status.PUBLISHED,
                publish=timezone.now()
            )

    def test_rss_feed_status_code(self):
        """Test the status code of the RSS feed page."""
        response = self.client.get(reverse('blog:post_feed'))
        self.assertEqual(response.status_code, 200)

    def test_rss_feed_content_type(self):
        """Test the Content-Type of the RSS feed page."""
        response = self.client.get(reverse('blog:post_feed'))
        self.assertEqual(response['Content-Type'], 'application/rss+xml; charset=utf-8')

    def test_rss_feed_contains_posts(self):
        """Test that the RSS feed contains posts."""
        response = self.client.get(reverse('blog:post_feed'))
        self.assertContains(response, 'RSS Test Post 0')
        self.assertContains(response, 'RSS Test Post 4')

    def test_rss_feed_item_count(self):
        """Test the number of items in the RSS feed (should be 5)."""
        feed = LatestPostsFeed()
        items = feed.items()
        self.assertEqual(len(items), 5)


class SearchTest(TestCase):
    """
    Test case for the search functionality.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # 登录用户
        self.client.login(username='testuser', password='testpass123')

        self.post1 = Post.objects.create(
            title='Django Search Test',
            slug='django-search-test',
            body='This is a Django related post.',
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )
        self.post2 = Post.objects.create(
            title='Python Search Test',
            slug='python-search-test',
            body='This is a Python related post.',
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )
        self.post3 = Post.objects.create(
            title='JavaScript Search Test',
            slug='javascript-search-test',
            body='This is a JavaScript related post.',
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )

    def test_search_by_body(self):
        response = self.client.get(reverse('blog:post_search'), {'query': 'JavaScript'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'JavaScript Search Test')

    def test_search_by_title(self):
        response = self.client.get(reverse('blog:post_search'), {'query': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Search Test')

    def test_search_empty_query(self):
        response = self.client.get(reverse('blog:post_search'), {'query': ''})
        self.assertEqual(response.status_code, 200)

    def test_search_no_results(self):
        response = self.client.get(reverse('blog:post_search'), {'query': 'NonexistentTerm'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Found 0 Results')
        self.assertEqual(len(response.context['results']), 0)


class BlogRouteIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='routeuser',
            email='route@example.com',
            password='testpass123'
        )

        self.primary_post = Post.objects.create(
            title='Integrated Route Post',
            slug='integrated-route-post',
            body='Primary post body.',
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )
        self.primary_post.tags.add('integration', 'routing')

        for i in range(4):
            post = Post.objects.create(
                title=f'Similar Route Post {i}',
                slug=f'similar-route-post-{i}',
                body=f'Similar post body {i}.',
                author=self.user,
                status=Post.Status.PUBLISHED,
                publish=timezone.now() + timezone.timedelta(minutes=i + 1)
            )
            post.tags.add('integration')

    def test_blog_homepage_route(self):
        response = self.client.get(reverse('blog:all_posts_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/all_posts_list.html')
        self.assertContains(response, 'Integrated Route Post')

    def test_blog_feed_route_is_public(self):
        response = self.client.get(reverse('blog:post_feed'))
        self.assertEqual(response.status_code, 200)

    def test_blog_search_route_is_public(self):
        response = self.client.get(reverse('blog:post_search'), {'query': 'Route'})
        self.assertEqual(response.status_code, 200)

    def test_blog_tag_route_is_public(self):
        response = self.client.get(reverse('blog:post_list_by_tag', kwargs={'tag_slug': 'integration'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/all_posts_list.html')

    def test_blog_detail_route(self):
        response = self.client.get(self.primary_post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/post_detail.html')
        self.assertContains(response, self.primary_post.title)

    def test_blog_create_route_requires_login(self):
        response = self.client.get(reverse('blog:post_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_blog_create_route_for_logged_in_user(self):
        self.client.login(username='routeuser', password='testpass123')
        response = self.client.get(reverse('blog:post_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/create_post.html')

    def test_blog_create_post_submission(self):
        self.client.login(username='routeuser', password='testpass123')
        image = BytesIO()
        Image.new('RGB', (1, 1), color='white').save(image, format='JPEG')
        image.name = 'cover.jpg'
        image.seek(0)

        response = self.client.post(
            reverse('blog:post_create'),
            {
                'title': 'Created By Test',
                'body': 'Created from integration test.',
                'tags': 'integration,test',
                'cover_image': image,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(title='Created By Test').exists())
        self.assertContains(response, 'Created By Test')

    def test_audio_list_route(self):
        AudioPost.objects.create(
            uploaded_by=self.user,
            audio_file='audio/2026/06/25/sample.mp3',
            description='Sample audio description',
            music_name='Sample Track'
        )
        response = self.client.get(reverse('blog:audio_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/audio/audio_list.html')
        self.assertContains(response, 'Sample Track')

    def test_audio_upload_post_submission(self):
        self.client.login(username='routeuser', password='testpass123')
        audio_content = BytesIO(b'ID3')
        audio_content.name = 'sample.mp3'
        response = self.client.post(
            reverse('blog:audio_upload'),
            {
                'music_name': 'Uploaded Sample',
                'description': 'Uploaded by integration test',
                'audio_file': audio_content,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AudioPost.objects.filter(music_name='Uploaded Sample').exists())
        self.assertContains(response, 'Uploaded Sample')

    def test_audio_upload_route_requires_login(self):
        response = self.client.post(
            reverse('blog:audio_upload'),
            {
                'music_name': 'Denied Upload',
                'description': 'Should redirect to login',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_audio_edit_route_requires_login(self):
        audio = AudioPost.objects.create(
            uploaded_by=self.user,
            audio_file='audio/2026/06/25/sample.mp3',
            description='Sample audio description',
            music_name='Sample Track'
        )
        self.client.logout()
        response = self.client.get(reverse('blog:audio_post_edit', kwargs={'pk': audio.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_audio_delete_route_requires_login(self):
        audio = AudioPost.objects.create(
            uploaded_by=self.user,
            audio_file='audio/2026/06/25/sample.mp3',
            description='Sample audio description',
            music_name='Sample Track'
        )
        self.client.logout()
        response = self.client.get(reverse('blog:audio_post_delete', kwargs={'pk': audio.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_audio_delete_get_only_shows_confirmation(self):
        self.client.login(username='routeuser', password='testpass123')
        audio = AudioPost.objects.create(
            uploaded_by=self.user,
            audio_file='audio/2026/06/25/sample.mp3',
            description='Sample audio description',
            music_name='Sample Track'
        )
        response = self.client.get(reverse('blog:audio_post_delete', kwargs={'pk': audio.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AudioPost.objects.filter(pk=audio.pk).exists())

    def test_audio_edit_rejects_non_owner(self):
        owner = User.objects.create_user(username='audioowner', password='testpass123')
        audio = AudioPost.objects.create(
            uploaded_by=owner,
            audio_file='audio/2026/06/25/sample.mp3',
            description='Owner audio',
            music_name='Owner Track'
        )
        self.client.login(username='routeuser', password='testpass123')
        response = self.client.post(
            reverse('blog:audio_post_edit', kwargs={'pk': audio.pk}),
            {
                'music_name': 'Hacked Track',
                'description': 'Changed by another user',
                'audio_file': SimpleUploadedFile('clip.mp3', b'ID3 sample audio bytes', content_type='audio/mpeg'),
            },
        )
        self.assertEqual(response.status_code, 403)
        audio.refresh_from_db()
        self.assertEqual(audio.music_name, 'Owner Track')

    def test_audio_delete_rejects_non_owner(self):
        owner = User.objects.create_user(username='audioowner2', password='testpass123')
        audio = AudioPost.objects.create(
            uploaded_by=owner,
            audio_file='audio/2026/06/25/sample.mp3',
            description='Owner audio',
            music_name='Owner Track'
        )
        self.client.login(username='routeuser', password='testpass123')
        response = self.client.post(reverse('blog:audio_post_delete', kwargs={'pk': audio.pk}))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(AudioPost.objects.filter(pk=audio.pk).exists())

    def test_comment_post_requires_login(self):
        response = self.client.post(
            reverse('blog:post_comment', kwargs={'post_id': self.primary_post.id}),
            {'body': 'Anonymous comment attempt'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_comment_post_submission_creates_comment(self):
        self.client.login(username='routeuser', password='testpass123')
        response = self.client.post(
            reverse('blog:post_comment', kwargs={'post_id': self.primary_post.id}),
            {'body': 'Integration comment'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Comment.objects.filter(post=self.primary_post, author=self.user, body='Integration comment').exists()
        )

    def test_edit_comment_rejects_non_owner(self):
        owner = User.objects.create_user(username='commentowner', password='testpass123')
        comment = Comment.objects.create(
            post=self.primary_post,
            author=owner,
            email='owner@example.com',
            body='Owner comment',
            active=True,
        )
        self.client.login(username='routeuser', password='testpass123')
        response = self.client.post(
            reverse('blog:edit_comment', kwargs={'post_slug': self.primary_post.slug, 'comment_id': comment.id}),
            {'body': 'Malicious edit'},
        )
        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertEqual(comment.body, 'Owner comment')

    def test_delete_comment_rejects_non_owner(self):
        owner = User.objects.create_user(username='commentowner', password='testpass123')
        Comment.objects.create(
            post=self.primary_post,
            author=owner,
            email='owner@example.com',
            body='Owner comment',
            active=True,
        )
        comment = Comment.objects.get(author=owner)
        self.client.login(username='routeuser', password='testpass123')
        response = self.client.post(
            reverse('blog:comment_delete', kwargs={'post_slug': self.primary_post.slug, 'comment_id': comment.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())

    def test_comment_delete_get_only_shows_confirmation(self):
        self.client.login(username='routeuser', password='testpass123')
        comment = Comment.objects.create(
            post=self.primary_post,
            author=self.user,
            email='route@example.com',
            body='Own comment',
            active=True,
        )
        response = self.client.get(
            reverse('blog:comment_delete', kwargs={'post_slug': self.primary_post.slug, 'comment_id': comment.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())


class UploadValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='uploaduser',
            email='upload@example.com',
            password='testpass123'
        )
        self.client.login(username='uploaduser', password='testpass123')

    def test_audio_upload_accepts_multipart_submission(self):
        audio_file = SimpleUploadedFile('clip.mp3', b'ID3 sample audio bytes', content_type='audio/mpeg')
        response = self.client.post(
            reverse('blog:audio_upload'),
            {
                'music_name': 'Multipart Audio',
                'description': 'Audio upload test',
                'audio_file': audio_file,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AudioPost.objects.filter(music_name='Multipart Audio').exists())

    def test_audio_upload_rejects_disallowed_file_type(self):
        audio_file = SimpleUploadedFile('clip.txt', b'not audio', content_type='text/plain')
        response = self.client.post(
            reverse('blog:audio_upload'),
            {
                'music_name': 'Bad Audio',
                'description': 'Invalid upload',
                'audio_file': audio_file,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AudioPost.objects.filter(music_name='Bad Audio').exists())
        self.assertContains(response, 'Audio upload must be an MP3, WAV, or OGG file.')

    def test_post_create_requires_image_under_form_processing(self):
        oversized_name = 'plain.txt'
        oversized_file = SimpleUploadedFile(oversized_name, b'not-an-image', content_type='text/plain')
        response = self.client.post(
            reverse('blog:post_create'),
            {
                'title': 'Bad Upload',
                'body': 'Should fail image validation.',
                'tags': 'upload,test',
                'cover_image': oversized_file,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Post.objects.filter(title='Bad Upload').exists())

    def test_post_create_rejects_oversized_cover_image(self):
        oversized = SimpleUploadedFile(
            'cover.webp',
            b'RIFF1234WEBPVP8 ' + (b'a' * (3 * 1024 * 1024 + 1)),
            content_type='image/webp',
        )
        response = self.client.post(
            reverse('blog:post_create'),
            {
                'title': 'Oversized Cover',
                'body': 'Should fail size validation.',
                'tags': 'upload,test',
                'cover_image': oversized,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Post.objects.filter(title='Oversized Cover').exists())
        self.assertContains(response, 'Upload a valid image.')


class BlogApiPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = User.objects.create_user(
            username='apiauthor',
            email='apiauthor@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='apiother',
            email='apiother@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='API Owned Post',
            slug='api-owned-post',
            body='Original body',
            author=self.author,
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )
        self.post.tags.add('api')
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            email='apiauthor@example.com',
            body='Original comment',
            active=True,
        )

    def test_post_detail_api_rejects_non_author_patch(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            reverse('blog:api_post_detail', kwargs={'pk': self.post.pk}),
            {'title': 'Hijacked Title'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'API Owned Post')

    def test_post_detail_api_allows_author_patch(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(
            reverse('blog:api_post_detail', kwargs={'pk': self.post.pk}),
            {'title': 'Updated By Author'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated By Author')

    def test_comment_detail_api_rejects_patch(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(
            reverse('blog:api_comment_detail', kwargs={'pk': self.comment.pk}),
            {'body': 'Changed comment'},
            format='json',
        )
        self.assertEqual(response.status_code, 405)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, 'Original comment')

    def test_comment_detail_api_rejects_delete(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.delete(reverse('blog:api_comment_detail', kwargs={'pk': self.comment.pk}))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())


class AdminTest(TestCase):
    """
    Test case for the admin interface.
    """

    def setUp(self):
        """Set up test data."""
        self.superuser = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client = Client()
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='regularpass123'
        )
        self.post = Post.objects.create(
            title='Admin Test Post',
            slug='admin-test-post',
            body='This is a test post for admin.',
            author=self.regular_user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )

    def test_admin_login_required(self):
        """Test that unauthenticated users cannot access the admin."""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)

    def test_admin_login_success(self):
        """Test that an admin user can log in successfully."""
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Site administration')

    def test_admin_post_list_accessible(self):
        """Test that the admin can access the post list page."""
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get('/admin/blog/post/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Test Post')

    def test_admin_post_change_accessible(self):
        """Test that the admin can access the post change page."""
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(f'/admin/blog/post/{self.post.id}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h2>Admin Test Post</h2>', html=True)

    def test_admin_post_delete(self):
        """Test that the admin can delete a post."""
        self.client.login(username='adminuser', password='adminpass123')
        post_id = self.post.id
        response = self.client.post(f'/admin/blog/post/{post_id}/delete/', {
            'post': post_id,
            'action': 'delete_selected',
            'index': 0,
            '_selected_action': [post_id],
            '_save': 'Save'
        }, follow=True)
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=post_id)


class DockerTest(TestCase):
    """
    Test case for Docker environment configuration.
    Note: These tests must be run on the host machine, not inside the container.
    """

    @unittest.skip("Docker tests must be run on the host machine")
    def test_db_container_running(self):
        """Test that the PostgreSQL database container is running."""
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=my_site_db', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertIn('my_site_db', result.stdout.strip())

    @unittest.skip("Docker tests must be run on the host machine")
    def test_web_container_running(self):
        """Test that the web container is running."""
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=my_site_web', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertIn('my_site_web', result.stdout.strip())

    @unittest.skip("Docker tests must be run on the host machine")
    def test_container_health_check(self):
        """Test the health status of the container."""
        result = subprocess.run(
            ['docker', 'inspect', 'my_site_web', '--format', '{{.State.Health.Status}}'],
            capture_output=True,
            text=True,
            check=True
        )
        health_status = result.stdout.strip()
        self.assertIn(health_status, ['healthy', 'starting'])

    @unittest.skip("Docker tests must be run on the host machine")
    def test_docker_compose_project(self):
        """Test that the Docker Compose project is running correctly."""
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertIn('my_site_web', result.stdout)
        self.assertIn('my_site_db', result.stdout)

# blog/tests.py
class RSSFeedTest(TestCase):
    def setUp(self):
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # 登录用户
        self.client.login(username='testuser', password='testpass123')
        # 创建 5 篇测试文章
        for i in range(5):
            Post.objects.create(
                title=f'RSS Test Post {i}',
                slug=f'rss-test-post-{i}',
                body=f'This is RSS test post {i} body.',
                author=self.user,
                status=Post.Status.PUBLISHED,
                publish=timezone.now()
            )
