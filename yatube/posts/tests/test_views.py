from django.test import Client, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.urls import reverse
from django import forms

from ..models import User, Group, Post, Comment, Follow
from ..consts import POSTS_NUMBERS


USERNAME = 'author'
ANOTHER_USERNAME = 'another_author'
SLUG = 'slug'
ANOTHER_SLUG = 'another_slug'
TEXT = 'Тут какой-то текст:)'


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )
        cls.user = User.objects.create_user(username=USERNAME)
        cls.another_user = User.objects.create_user(username=ANOTHER_USERNAME)
        cls.group = Group.objects.create(slug=SLUG)
        cls.another_group = Group.objects.create(slug=ANOTHER_SLUG)
        cls.post = Post.objects.create(
            text=TEXT, author=cls.user, group=cls.group, image=uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post, author=cls.user, text=TEXT
        )
        cls.url_address_map = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ),
            'profile': reverse(
                'posts:profile', kwargs={'username': cls.user.username}
            ),
            'post_detail': reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.id}
            ),
            'create': reverse('posts:create'),
            'edit': reverse(
                'posts:edit', kwargs={'post_id': f'{cls.post.id}'}
            ),
            'another_group_list': reverse(
                'posts:group_list', kwargs={'slug': cls.another_group.slug}
            ),
            'follow': reverse(
                'posts:profile_follow',
                kwargs={'username': cls.another_user.username},
            ),
            'unfollow': reverse(
                'posts:profile_unfollow',
                kwargs={'username': cls.another_user.username},
            ),
            'follow_index': reverse('posts:follow_index'),
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.not_follower_client = Client()
        self.not_follower_client.force_login(self.another_user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            self.url_address_map['index']: 'posts/index.html',
            self.url_address_map['group_list']: 'posts/group_list.html',
            self.url_address_map['profile']: 'posts/profile.html',
            self.url_address_map['post_detail']: 'posts/post_detail.html',
            self.url_address_map['create']: 'posts/create.html',
            self.url_address_map['edit']: 'posts/create.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_context(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.url_address_map['index'])
        post = response.context['page_obj'][0]
        self.check_context(post)

    def test_group_posts_pages_show_correct_context(self):
        """Шаблон group_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.url_address_map['group_list']
        )
        post = response.context['page_obj'][0]
        self.check_context(post)
        group = response.context['group']
        self.assertEqual(group.slug, self.group.slug)

    def test_profile_pages_show_correct_context(self):
        """Шаблон group_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.url_address_map['profile'])
        post = response.context['page_obj'][0]
        self.check_context(post)
        self.assertEqual(post.author, self.user)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.url_address_map['post_detail']
        )
        post = response.context['post']
        self.check_context(post)
        comment = response.context['comments'][0]
        self.assertEqual(comment, self.comment)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.url_address_map['create'])
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.url_address_map['edit'])
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_doesnt_appear_in_another_group(self):
        """Проверка, что пост не попал в другую группу."""
        response = self.authorized_client.get(
            self.url_address_map['another_group_list']
        )
        posts = response.context['page_obj']
        self.assertEqual(len(posts), 0)

    def test_cache_index_page(self):
        """Проверка кеширования главной страницы"""
        response = self.authorized_client.get(self.url_address_map['index'])
        self.post.delete()
        cached_response = self.authorized_client.get(
            self.url_address_map['index']
        )
        self.assertEqual(response.content, cached_response.content)
        cache.clear()
        fresh_response = self.authorized_client.get(
            self.url_address_map['index']
        )
        self.assertNotEqual(response.content, fresh_response.content)

    def test_authorized_client_can_follow_another_authors(self):
        """Проверка что авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок"""
        follows_count = Follow.objects.count()
        self.authorized_client.get(
            self.url_address_map['follow'], args=(self.another_user,)
        )
        new_follows_count = Follow.objects.count()
        self.assertEqual(new_follows_count, follows_count + 1)

        self.assertTrue(
            Follow.objects.filter(
                user=self.user, author=self.another_user
            ).exists()
        )
        self.authorized_client.get(
            self.url_address_map['unfollow'], args=(self.another_user,)
        )
        new_follows_count_after_unfollow = Follow.objects.count()
        self.assertEqual(new_follows_count_after_unfollow, follows_count)

    def test_new_post_appear_in_followers_pages(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан"""
        post = Post.objects.create(text=TEXT, author=self.another_user)
        Follow.objects.create(user=self.user, author=self.another_user)
        response = self.authorized_client.get(
            self.url_address_map['follow_index']
        )
        self.assertEqual(response.context['page_obj'][0], post)
        response = self.not_follower_client.get(
            self.url_address_map['follow_index']
        )
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(slug='slug')
        cls.SECOND_PAGE_COUNT = 3
        posts_lst = []
        for i in range(POSTS_NUMBERS + cls.SECOND_PAGE_COUNT):
            posts_lst.append(
                Post(
                    text='Тут много-много-много текста :)',
                    author=cls.user,
                    group=cls.group,
                )
            )
        Post.objects.bulk_create(posts_lst)

        cls.url_address_lst = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:profile', kwargs={'username': cls.user.username}),
        ]

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_and_second_pages_contain_correct_records(self):
        """Проверка пагинатора"""

        for url_address in self.url_address_lst:
            response = self.client.get(url_address)
            self.assertEqual(len(response.context['page_obj']), POSTS_NUMBERS)
            response = self.client.get(url_address + '?page=2')
            self.assertEqual(
                len(response.context['page_obj']), self.SECOND_PAGE_COUNT
            )
