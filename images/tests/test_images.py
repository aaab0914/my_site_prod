from io import BytesIO

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from images.models import ImagePost


class ImagePostModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def create_test_image(self):
        image = Image.new("RGB", (100, 100), color="red")
        image_io = BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)
        return SimpleUploadedFile(
            name="test_image.jpg",
            content=image_io.getvalue(),
            content_type="image/jpeg",
        )

    def test_create_image_post_and_string_representation(self):
        image_post = ImagePost.objects.create(
            title="Test Image",
            image=self.create_test_image(),
            description="Test description",
            uploaded_by=self.user,
        )
        self.assertEqual(image_post.title, "Test Image")
        self.assertEqual(image_post.uploaded_by, self.user)
        self.assertEqual(image_post.description, "Test description")
        self.assertEqual(str(image_post), "Test Image")
        self.assertIsNotNone(image_post.created)
        self.assertIsNotNone(image_post.updated)

    def test_image_post_is_deleted_when_user_is_deleted(self):
        image_post = ImagePost.objects.create(
            title="Test Image",
            image=self.create_test_image(),
            uploaded_by=self.user,
        )
        image_post_id = image_post.id
        self.user.delete()
        self.assertFalse(ImagePost.objects.filter(id=image_post_id).exists())
