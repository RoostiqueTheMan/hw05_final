from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testoviy_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

    def test_urls_exists(self):
        """Тест проверки доступности адресов /"""
        url_names = {
            '/',
            f'/group/{PostsURLTests.group.slug}/',
            f'/profile/{PostsURLTests.user.username}/',
            f'/posts/{PostsURLTests.post.pk}/',
            '/create/',
            f'/posts/{PostsURLTests.post.pk}/',
        }

        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_unknown_url_not_exist(self):
        """Тест вывода ошибки 404 на несуществующую страницу"""
        response = self.guest_client.get('/wtf/')
        self.assertEqual(response.status_code, 404)

    def test_post_create_url_redirect_anonymous(self):
        """
        Тест проверки редиректа неавторизованного пользователя
        для ссылки вида /create/
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_anonymous(self):
        """
        Тест проверки редиректа неаторизованного пользователя
        для ссылки вида /posts/<post_id>/edit/
        """

        response = self.guest_client.get(
            f'/posts/{PostsURLTests.post.pk}/edit/', follow=True)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostsURLTests.post.pk}/edit/'
        )

    def test_post_edit_url_redirect_authorized(self):
        """
        Тест на недоступность изменения поста сторонним пользователем
        """

        another_user = User.objects.create_user(username='auth_2')
        authorized_client_2 = Client()
        authorized_client_2.force_login(another_user)

        response = authorized_client_2.get(
            f'/posts/{PostsURLTests.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(response, f'/posts/{PostsURLTests.post.pk}/')

    def test_urls_uses_correct_template(self):
        """Тест на использование корректных шаблонов"""

        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostsURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostsURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostsURLTests.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{PostsURLTests.post.pk}/edit/': 'posts/create_post.html',
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
