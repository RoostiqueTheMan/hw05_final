from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='testoviy slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Этот текст для проверки тестового поста 1',
            group=cls.group
        )

    def test_models_have_correct_str_method(self):
        """Проверяем, что у моделей корректно работает str."""

        str_method_results = {
            self.post: self.post.text[:15],
            self.group: self.group.title,
        }

        for model_with_str_method, result in str_method_results.items():
            with self.subTest(model_with_str_method=model_with_str_method):
                self.assertEqual(
                    str(model_with_str_method),
                    result,
                    'Функция str в модели Post работает неверно'
                )
