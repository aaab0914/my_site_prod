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

from .models import Post, Comment
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

import subprocess
# subprocess: Module for running external commands

import unittest
# unittest: Python's built-in unit testing framework


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