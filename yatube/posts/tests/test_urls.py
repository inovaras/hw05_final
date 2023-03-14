from http import HTTPStatus
from django.test import TestCase, Client

from ..models import Group, Post, User


USERNAME = 'user'
AUTHOR = 'author'
SLUG = 'some_slug'
TEXT = 'some text'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.group = Group.objects.create(slug=SLUG)
        cls.post = Post.objects.create(
            text=TEXT, author=cls.author, group=cls.group
        )
        cls.access_url_address_map = {
            '/': 'all',
            f'/group/{cls.group.slug}/': 'all',
            f'/profile/{cls.user.username}/': 'all',
            f'/posts/{cls.post.id}/': 'all',
            '/create/': 'authorized',
            '/follow/': 'authorized',
            f'/posts/{cls.post.id}/edit/': 'author',
            f'/profile/{cls.user.username}/follow/': 'authorized',
            f'/profile/{cls.user.username}/unfollow/': 'authorized',
            f'/posts/{cls.post.id}/comment/': 'authorized',
        }
        cls.template_url_name = {
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create.html',
            '/follow/': 'posts/follow.html',
            f'/profile/{cls.user.username}/follow/': 'posts/profile.html',
            f'/profile/{cls.user.username}/unfollow/': 'posts/profile.html',
            f'/posts/{cls.post.id}/comment/': 'posts/post_detail.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        for address, template in self.template_url_name.items():
            with self.subTest(address=address):
                response = self.author_client.get(address, follow=True)
                self.assertTemplateUsed(response, template)

    def test_url_access_for_authorized_only(self):
        """Страницы, доступные только авторизованным пользователям"""
        for (
            address,
            access,
        ) in self.access_url_address_map.items():
            if access == 'authorized':
                with self.subTest(address=address):
                    response = self.authorized_client.get(address, follow=True)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_access_for_all(self):
        """Страницы, доступные всем пользователям"""
        for (
            address,
            access,
        ) in self.access_url_address_map.items():
            if access == 'all':
                with self.subTest(address=address):
                    response = self.guest_client.get(address, follow=True)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_access_for_author_only(self):
        """Страницы, доступные только автору"""
        for (
            address,
            access,
        ) in self.access_url_address_map.items():
            if access == 'author':
                with self.subTest(address=address):
                    response = self.author_client.get(address, follow=True)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
