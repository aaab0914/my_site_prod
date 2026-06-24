from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO
from .models import ImagePost


class ImagePostModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def create_test_image(self):
        """Helper method to create a test image"""
        image = Image.new('RGB', (100, 100), color='red')
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=image_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_create_image_post(self):
        """Test creating an ImagePost"""
        image = self.create_test_image()
        image_post = ImagePost.objects.create(
            title='Test Image',
            image=image,
            description='Test description',
            uploaded_by=self.user
        )
        self.assertEqual(image_post.title, 'Test Image')
        self.assertEqual(image_post.uploaded_by, self.user)
        self.assertEqual(image_post.description, 'Test description')

    def test_image_post_str(self):
        """Test ImagePost string representation"""
        image = self.create_test_image()
        image_post = ImagePost.objects.create(
            title='Test Image',
            image=image,
            uploaded_by=self.user
        )
        self.assertEqual(str(image_post), 'Test Image')

    def test_image_post_created_timestamp(self):
        """Test created timestamp is set"""
        image = self.create_test_image()
        image_post = ImagePost.objects.create(
            title='Test Image',
            image=image,
            uploaded_by=self.user
        )
        self.assertIsNotNone(image_post.created)

    def test_image_post_updated_timestamp(self):
        """Test updated timestamp is set"""
        image = self.create_test_image()
        image_post = ImagePost.objects.create(
            title='Test Image',
            image=image,
            uploaded_by=self.user
        )
        self.assertIsNotNone(image_post.updated)

    def test_image_post_description_optional(self):
        """Test description is optional"""
        image = self.create_test_image()
        image_post = ImagePost.objects.create(
            title='Test Image',
            image=image,
            uploaded_by=self.user
        )
        self.assertEqual(image_post.description, '')

    def test_image_post_delete_with_user(self):
        """Test ImagePost is deleted when user is deleted"""
        image = self.create_test_image()
        image_post = ImagePost.objects.create(
            title='Test Image',
            image=image,
            uploaded_by=self.user
        )
        image_post_id = image_post.id
        self.user.delete()
        self.assertFalse(ImagePost.objects.filter(id=image_post_id).exists())

    def test_multiple_images_by_same_user(self):
        """Test multiple images can be uploaded by same user"""
        image1 = self.create_test_image()
        image2 = self.create_test_image()
        ImagePost.objects.create(
            title='Image 1',
            image=image1,
            uploaded_by=self.user
        )
        ImagePost.objects.create(
            title='Image 2',
            image=image2,
            uploaded_by=self.user
        )
        self.assertEqual(ImagePost.objects.filter(uploaded_by=self.user).count(), 2)
