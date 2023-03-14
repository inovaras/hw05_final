import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..models import Comment, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

AUTHOR = 'author'
SLUG = 'slug'
TEXT = 'Тут какой-то текст:)'
ANOTHER_TEXT = 'Тут другой текст'


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

        self.guess_client = Client()

    def test_create_post_authorized_client(self):
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

    def test_create_post_guess_client(self):
        """Невалидная форма не создает новый пост."""

        posts_count = Post.objects.count()

        form_data = {'text': ANOTHER_TEXT, 'group': self.group.pk}
        response = self.guess_client.post(
            reverse('posts:create'), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse('login') + '?next=' + reverse('posts:create'),
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'], group=form_data['group']
            ).exists()
        )

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

    def test_not_edit_post(self):
        """Невалидная форма не правит существующий пост"""

        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='new_small.gif',
            content=self.small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Тестовый заголовок',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.guess_client.post(
            reverse('posts:edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('login')
            + '?next='
            + reverse('posts:edit', kwargs={'post_id': self.post.id}),
        )
        self.assertEqual(Post.objects.count(), posts_count)

        post = Post.objects.first()
        self.assertNotEqual(post.text, form_data['text'])
        self.assertNotEqual(post.image.name, f'posts/{uploaded.name}')

    def test_authorized_user_can_leave_comments(self):
        """Авторизованный пользователь может оставлять комментарии"""

        comments_count = Comment.objects.count()
        form_data = {'text': TEXT}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)

        comment_first = Comment.objects.first()
        self.assertEqual(comment_first.text, form_data['text'])
        self.assertEqual(comment_first.post, self.post)
        self.assertEqual(comment_first.author, self.user)

    def test_guess_user_can_leave_comments(self):
        """Гостевой пользователь не может оставлять комментарии"""

        comments_count = Comment.objects.count()
        form_data = {'text': TEXT}
        response = self.guess_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('login')
            + '?next='
            + reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(
            Comment.objects.filter(text=form_data['text']).exists()
        )
