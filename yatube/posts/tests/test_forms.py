import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

AUTHOR = 'author'
SLUG = 'slug'
TEXT = 'Тут какой-то текст:)'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR)
        cls.group = Group.objects.create(slug=SLUG)
        cls.post = Post.objects.create(
            text=TEXT, author=cls.user, group=cls.group
        )
        cls.form = PostForm()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает новый пост."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif', content=self.small_gif, content_type='image/gif'
        )
        form_data = {'text': TEXT, 'group': self.group.pk, 'image': uploaded}
        response = self.authorized_client.post(
            reverse('posts:create'), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username}),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image.name, f'posts/{uploaded.name}')

    def test_edit_post(self):
        """Валидная форма правит существующий пост"""

        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='edited_small.gif',
            content=self.small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Тестовый заголовок',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        )
        self.assertEqual(Post.objects.count(), posts_count)

        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image.name, f'posts/{uploaded.name}')
