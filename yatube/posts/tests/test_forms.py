import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Название',
            slug='Testoviy slug',
            description='Описание',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormsTests.user)

    def test_create_post_from_form(self):
        posts_count = Post.objects.count()

        form_data = {
            'text': "Тестовый пост",
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={
                'username': PostFormsTests.user.username
            }))
        self.assertNotEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост'
            ).exists()
        )

    def test_edit_post_from_form(self):
        post = Post.objects.create(
            text='Тестовый текст',
            author=PostFormsTests.user,
            group=PostFormsTests.group
        )

        posts_count = Post.objects.count()

        form_data = {
            'text': "Testovij tekst",
        }

        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={
                'post_id': post.pk
            }))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Testovij tekst'
            ).exists()
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class MediaTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Название',
            slug='testoviy_slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='Текст тестового поста',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(MediaTests.user)

    def test_create_image(self):
        tasks_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               args=(self.user.username,)))
        self.assertEqual(Post.objects.count(), tasks_count + 1)

    def test_decline_not_image(self):
        uploaded = SimpleUploadedFile(
            name='not_image.txt',
            content=b'toto'
        )

        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        error_text = (
            'Загрузите правильное изображение. '
            'Файл, который вы загрузили, поврежден '
            'или не является изображением.'
        )

        self.assertFormError(response, 'form', 'image', error_text)
