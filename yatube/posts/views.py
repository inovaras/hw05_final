from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .consts import POSTS_NUMBERS


@cache_page(20, key_prefix='index_page')
@vary_on_cookie
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POSTS_NUMBERS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).all()
    paginator = Paginator(post_list, POSTS_NUMBERS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = User.objects.get(username=username)
    post_list = Post.objects.filter(author=author)
    paginator = Paginator(post_list, POSTS_NUMBERS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=author).exists()
    )
    context = {'page_obj': page_obj, 'author': author, 'following': following}
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    form = CommentForm()
    post = Post.objects.get(id=post_id)
    comments = post.comments.all()
    context = {
        'post': post,
        'is_edit': True,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required()
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(
            request, 'posts/create.html', {'form': form, 'is_edit': False}
        )
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user.username)


@login_required()
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    post_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    paginator = Paginator(post_list, POSTS_NUMBERS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    is_following_already = Follow.objects.filter(
        user=user, author=author
    ).exists()
    if user != author and not is_following_already:
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()

    return redirect('posts:profile', username=username)
