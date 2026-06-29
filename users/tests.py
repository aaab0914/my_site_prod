from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from .models import Profile, UserActivity, UserPreference
from .forms import UserRegisterForm, UserLoginForm
from blog.models import Post, Comment


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')

    def test_profile_created_on_user_creation(self):
        """Test that Profile is created when User is created"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)

    def test_profile_str(self):
        """Test Profile string representation"""
        self.assertEqual(str(self.user.profile), 'testuser Profile')

    def test_can_change_avatar_first_time(self):
        """Test avatar change allowed on first change"""
        self.assertTrue(self.user.profile.can_change_avatar())

    def test_can_change_avatar_within_3_days(self):
        """Test avatar change blocked within 3 days"""
        self.user.profile.last_avatar_change = timezone.now()
        self.user.profile.save()
        self.assertFalse(self.user.profile.can_change_avatar())

    def test_can_change_avatar_after_3_days(self):
        """Test avatar change allowed after 3 days"""
        self.user.profile.last_avatar_change = timezone.now() - timedelta(days=3)
        self.user.profile.save()
        self.assertTrue(self.user.profile.can_change_avatar())

    def test_avatar_change_remaining_days(self):
        """Test remaining days calculation"""
        self.user.profile.last_avatar_change = timezone.now() - timedelta(days=1)
        self.user.profile.save()
        self.assertEqual(self.user.profile.get_avatar_change_remaining_days(), 2)

    def test_user_activity_creation(self):
        """Test UserActivity model"""
        activity = UserActivity.objects.create(
            user=self.user,
            action='login',
            ip_address='127.0.0.1'
        )
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.action, 'login')

    def test_user_preference_creation(self):
        """Test UserPreference model"""
        pref = UserPreference.objects.create(user=self.user, theme='dark')
        self.assertEqual(pref.theme, 'dark')
        self.assertTrue(pref.email_notifications)


class UserRegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('users:register')

    def test_register_page_loads(self):
        """Test GET register page"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_register_user_success(self):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123',
            'password2': 'SecurePass123'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertEqual(response.url, reverse('blog:all_posts_list'))

    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123',
            'password2': 'DifferentPass'
        }
        response = self.client.post(self.register_url, data)
        self.assertFalse(User.objects.filter(username='newuser').exists())


class UserLoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.login_url = reverse('users:login')
        cache.clear()

    def test_login_page_loads(self):
        """Test GET login page"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        """Test successful login"""
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_wrong_password(self):
        """Test login with wrong password"""
        data = {'username': 'testuser', 'password': 'wrongpass'}
        response = self.client.post(self.login_url, data)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_is_rate_limited_after_repeated_failures(self):
        data = {'username': 'testuser', 'password': 'wrongpass'}
        for _ in range(5):
            self.client.post(self.login_url, data)
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 429)


class UserRouteIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_route_is_available_for_blog_redirects(self):
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)

    def test_register_route_is_available_for_blog_redirects(self):
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)

    def test_profile_route_requires_login_for_own_profile(self):
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_edit_requires_login(self):
        response = self.client.get(reverse('users:profile_edit'))
        self.assertEqual(response.status_code, 302)

    def test_username_change_requires_login(self):
        response = self.client.post(reverse('users:username_change'), {'username': 'newname'})
        self.assertEqual(response.status_code, 302)

    def test_account_delete_requires_login_for_post(self):
        response = self.client.post(reverse('users:account_delete'), {'confirm_delete': True})
        self.assertEqual(response.status_code, 302)


class UserProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_view_own_profile(self):
        """Test viewing own profile"""
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], self.user)

    def test_view_other_profile(self):
        """Test viewing other user's profile"""
        other_user = User.objects.create_user(username='otheruser', password='pass')
        response = self.client.get(reverse('users:profile_by_username', kwargs={'username': 'otheruser'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], other_user)

    def test_view_other_profile_hides_draft_posts_and_inactive_comments(self):
        other_user = User.objects.create_user(username='otheruser', password='pass')
        published_post = Post.objects.create(
            title='Published profile post',
            slug='published-profile-post',
            body='Visible post body',
            author=other_user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )
        published_post.tags.add('profile')
        Post.objects.create(
            title='Draft profile post',
            slug='draft-profile-post',
            body='Hidden draft body',
            author=other_user,
            status=Post.Status.DRAFT,
            publish=timezone.now(),
        )
        Comment.objects.create(
            post=published_post,
            author=other_user,
            email='other@example.com',
            body='Visible comment',
            active=True,
        )
        Comment.objects.create(
            post=published_post,
            author=other_user,
            email='other@example.com',
            body='Hidden comment',
            active=False,
        )

        response = self.client.get(reverse('users:profile_by_username', kwargs={'username': 'otheruser'}))
        self.assertEqual(response.status_code, 200)
        posts = list(response.context['posts'])
        comments = list(response.context['comments'])
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].title, 'Published profile post')
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].body, 'Visible comment')

    def test_view_own_profile_keeps_draft_posts_and_all_comments(self):
        published_post = Post.objects.create(
            title='Own published post',
            slug='own-published-post',
            body='Visible post body',
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )
        published_post.tags.add('profile')
        Post.objects.create(
            title='Own draft post',
            slug='own-draft-post',
            body='Draft body',
            author=self.user,
            status=Post.Status.DRAFT,
            publish=timezone.now(),
        )
        Comment.objects.create(
            post=published_post,
            author=self.user,
            email='test@example.com',
            body='Active own comment',
            active=True,
        )
        Comment.objects.create(
            post=published_post,
            author=self.user,
            email='test@example.com',
            body='Inactive own comment',
            active=False,
        )

        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['posts'].count(), 2)
        self.assertEqual(response.context['comments'].count(), 2)

    def test_profile_not_found(self):
        """Test 404 for non-existent user"""
        response = self.client.get(reverse('users:profile_by_username', kwargs={'username': 'nonexistent'}))
        self.assertEqual(response.status_code, 404)

    def test_profile_edit_post_updates_non_file_fields(self):
        response = self.client.post(
            reverse('users:profile_edit'),
            {
                'bio': 'Updated bio',
                'location': 'Shanghai',
                'birth_date': '2000-01-01',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Updated bio')
        self.assertEqual(self.user.profile.location, 'Shanghai')

    def test_profile_edit_avatar_upload_respects_login_flow(self):
        avatar = SimpleUploadedFile('avatar.jpg', b'avatar-bytes', content_type='image/jpeg')
        response = self.client.post(
            reverse('users:profile_edit'),
            {
                'bio': 'Avatar update',
                'location': 'Beijing',
                'birth_date': '2001-02-03',
                'avatar': avatar,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_profile_edit_rejects_disallowed_avatar_type(self):
        avatar = SimpleUploadedFile(
            'avatar.webp',
            b'RIFF1234WEBPVP8 ',
            content_type='image/webp',
        )
        response = self.client.post(
            reverse('users:profile_edit'),
            {
                'bio': 'Avatar update',
                'location': 'Beijing',
                'birth_date': '2001-02-03',
                'avatar': avatar,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload a valid image.')


class UserAccountDeleteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.delete_url = reverse('users:account_delete')

    def test_delete_page_loads(self):
        """Test GET delete confirmation page"""
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)

    def test_delete_account_success(self):
        """Test successful account deletion"""
        user_id = self.user.id
        response = self.client.post(self.delete_url, {'confirm_delete': True})
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_delete_account_get_only_shows_confirmation(self):
        user_id = self.user.id
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(id=user_id).exists())

    def test_delete_requires_login(self):
        """Test delete requires authentication"""
        self.client.logout()
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 302)


class UsernameChangeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('users:username_change')

    def test_change_username_success(self):
        """Test successful username change"""
        response = self.client.post(self.url, {'username': 'newusername'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')

    def test_change_to_existing_username(self):
        """Test cannot change to existing username"""
        User.objects.create_user(username='existinguser', password='pass')
        response = self.client.post(self.url, {'username': 'existinguser'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')

    def test_change_to_existing_username_case_insensitive(self):
        User.objects.create_user(username='ExistingUser', password='pass')
        response = self.client.post(self.url, {'username': 'existinguser'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')

    def test_change_username_rejects_invalid_characters(self):
        response = self.client.post(self.url, {'username': 'bad name'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')

    def test_change_username_rejects_empty_value(self):
        response = self.client.post(self.url, {'username': '   '}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')

    def test_change_username_rejects_overlong_value(self):
        response = self.client.post(self.url, {'username': 'a' * 151}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')
