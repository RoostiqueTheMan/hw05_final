from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Comment

User = get_user_model()


class ViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create(username='auth_1')
        cls.group = Group.objects.create(
            title='Название',
            slug='testoviy_slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='Текст тестового поста',
            author=cls.user_1,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(ViewTests.user_1)
        cache.clear()

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',

            reverse(
                'posts:group_list',
                kwargs={'slug': ViewTests.group.slug}
            ): 'posts/group_list.html',

            reverse(
                'posts:profile',
                kwargs={'username': ViewTests.user_1.username}
            ): 'posts/profile.html',

            reverse(
                'posts:post_detail',
                kwargs={'post_id': ViewTests.post.pk}
            ): 'posts/post_detail.html',

            reverse(
                'posts:post_edit',
                kwargs={'post_id': ViewTests.post.pk}
            ): 'posts/create_post.html',

            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_list_profile_show_correct_context(self):
        reversed_names = [
            reverse('posts:index'),
            reverse(
                'posts:profile',
                kwargs={'username': ViewTests.user_1.username}
            ),
            reverse('posts:group_list', kwargs={'slug': ViewTests.group.slug})
        ]

        for reversed_name in reversed_names:
            with self.subTest(reversed_name=reversed_name):
                response = self.authorized_client.get(reversed_name)
                object = response.context['page_obj'][-1]

                test_text = object.text
                test_author = object.author
                test_group = object.group
                self.assertEqual(test_text, 'Текст тестового поста')
                self.assertEqual(test_author.username, 'auth_1')
                self.assertEqual(test_group.title, 'Название')

    def test_post_detail_pages_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': ViewTests.post.pk})
        )
        self.assertEqual(
            response.context['post'].text, 'Текст тестового поста')
        self.assertEqual(response.context['post'].group, ViewTests.group)

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': ViewTests.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_new_created_post_is_on_home_group_profile_pages(self):
        group_2 = Group.objects.create(
            title='Название1',
            slug='test-slug1',
            description='Описание1',
        )
        post_2 = Post.objects.create(
            text='Текст тестового поста',
            author=ViewTests.user_1,
            group=group_2,
        )

        templates_pages_names = [
            reverse('posts:index'),

            reverse(
                'posts:group_list',
                kwargs={'slug': group_2.slug}
            ),

            reverse(
                'posts:profile',
                kwargs={'username': ViewTests.user_1.username}
            )
        ]
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.context.get(
                    'page_obj').object_list[0], post_2)

    def test_new_post_not_in_another_group_page(self):
        group_2 = Group.objects.create(
            title='Название1',
            slug='test-slug1',
            description='Описание1',
        )

        post_2 = Post.objects.create(
            text='Текст тестового поста',
            author=ViewTests.user_1,
            group=group_2,
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': ViewTests.group.slug}
            )
        )
        self.assertNotEqual(response.context.get(
            'page_obj').object_list[0], post_2)

    def test_correct_image_context(self):
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

        post = Post.objects.create(
            author=self.user_1,
            group=self.group,
            text='Тестовый пост с картинкой',
            image=uploaded,
        )

        reversed_urls = (
            reverse('posts:index'),
            reverse('posts:profile', args=(self.user_1.username,)),
            reverse('posts:post_detail', args=(post.id,)),
            reverse('posts:group_list', args=(self.group.slug,))
        )

        for url in reversed_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertContains(response, '<img')

    def test_auth_user_can_comment(self):
        comment_text = 'test comment'
        self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data={'text': comment_text})
        comments_len = self.post.comments.count()
        self.assertEqual(comments_len, 1)
        comment = self.post.comments.first()
        self.assertEqual(comment.text, comment_text)

    def test_comment_in_post_detail_page(self):
        comment = Comment.objects.create(
            author=self.user_1,
            text='test comment',
            post=self.post
        )
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      args=(self.post.id,)))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, comment.text)

    def test_cache(self):
        index = reverse('posts:index')

        post_two = Post.objects.create(
            text='Кэирование',
            author=self.user_1
        )

        response_clear = self.authorized_client.get(index)
        post_two.delete()
        response_cache = self.authorized_client.get(index)

        self.assertEqual(
            response_clear.content,
            response_cache.content
        )

        cache.clear()
        response_without = self.authorized_client.get(index)

        self.assertNotEqual(
            response_clear.content,
            response_without.content
        )


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_2 = User.objects.create_user(username='auth_2')
        cls.group = Group.objects.create(
            title='Название',
            slug='test-slug',
            description='Описание',
        )
        cls.posts = []
        for i in range(0, 13):
            cls.posts.append(Post.objects.create(
                text=f'Текст тестового поста{i}',
                author=cls.user_2,
                group=cls.group,
            ))

    def setUp(self):
        self.client_2 = Client()
        self.client_2.force_login(PaginatorTests.user_2)

    def test_first_page_contains_ten_posts(self):
        reverse_name = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={
                    'username': PaginatorTests.user_2.username}),
            reverse('posts:group_list', kwargs={
                    'slug': PaginatorTests.group.slug})
        ]
        for reversed_name in reverse_name:
            with self.subTest(reversed_name=reversed_name):
                response = self.client_2.get(reversed_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_posts(self):
        reverse_name = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={
                    'username': PaginatorTests.user_2.username}),
            reverse('posts:group_list', kwargs={
                    'slug': PaginatorTests.group.slug})
        ]
        for reversed_name in reverse_name:
            with self.subTest(reversed_name=reversed_name):
                response = self.client_2.get(reversed_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
