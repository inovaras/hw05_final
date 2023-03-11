from django.test import TestCase

from ..models import Group, Post, User, POST_TRUNCATE_NUMBER


TITLE = 'Некоторая группа'
SLUG = 'some_slug'
DESCRIPTION = 'Некоторое описание'
TEXT = 'Текст поста должен обрезаться по первым 15ти символам '


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title=TITLE,
            slug=SLUG,
            description=DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name = post.text[:POST_TRUNCATE_NUMBER]
        self.assertEqual(expected_object_name, str(post))
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
