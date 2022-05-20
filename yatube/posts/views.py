from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import POSTS_QUANTITY

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POSTS_QUANTITY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, POSTS_QUANTITY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, POSTS_QUANTITY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    post_quantity = author.posts.count()

    following = (
        request.user.is_authenticated
        and request.user.follower.filter(author__username=username).exists()
    )

    context = {
        'author': author,
        'page_obj': page_obj,
        'post_quantity': post_quantity,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_quantity = post.author.posts.count()
    comment_form = CommentForm()
    comments = post.comments.select_related('author')

    context = {
        'post': post,
        'post_quantity': post_quantity,
        'comments': comments,
        'comment_form': comment_form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(f'/profile/{request.user}/')
    return render(request, 'posts/create_post.html', {'form': form})


@ login_required
def post_edit(request, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id)

    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@ login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@ login_required
def follow_index(request):
    posts = Post.objects.select_related().filter(
        author__following__user=request.user)

    page_number = request.GET.get('page')

    paginator = Paginator(posts, POSTS_QUANTITY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    template = 'posts/follow.html'
    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


@ login_required
def profile_follow(request, username):

    is_follow = request.user.follower.filter(
        author__username=username).exists()

    author_user = User.objects.get(username=username)

    if not is_follow and request.user != author_user:
        follow = Follow.objects.create(
            user=request.user,
            author=User.objects.get(username=username)
        )
        follow.save()

    return redirect('posts:profile', username=username)


@ login_required
def profile_unfollow(request, username):

    follow = Follow.objects.filter(
        user=request.user,
        author__username=username
    )

    follow.delete()

    return redirect('posts:profile', username=username)
