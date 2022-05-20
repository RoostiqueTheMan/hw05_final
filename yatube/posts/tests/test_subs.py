from posts.models import Follow, Post, User
from django.urls import reverse
from django.test import Client, TestCase


class SubsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.author = User.objects.create(username='author')

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_user_can_subscribe(self):
        followers_number = self.user.follower.count()
        url = reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}
        )
        result = reverse(
            'posts:profile',
            kwargs={'username': self.author.username}
        )

        response = self.authorized_client.get(url, follow=True)

        self.assertRedirects(response, result)
        self.assertTrue(followers_number < self.user.follower.count())
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author,
            ).exists()
        )

    def test_user_can_unsubscribe(self):
        Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        followers_number = self.user.follower.count()

        url = reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username}
        )
        result = reverse(
            'posts:profile',
            kwargs={'username': self.author.username}
        )

        response = self.authorized_client.get(
            url,
            follow=True
        )

        self.assertRedirects(response, result)
        self.assertTrue(followers_number > self.user.follower.count())
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author,
            ).exists()
        )

    def test_follows_feed(self):
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.author
        )

        url = reverse('posts:follow_index')
        response = self.authorized_client.get(url)
        subscribe_posts = response.context.get('page_obj').object_list
        self.assertNotIn(post, subscribe_posts)

        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response = self.authorized_client.get(url)
        subscribe_posts = response.context.get('page_obj').object_list
        self.assertIn(post, subscribe_posts)
