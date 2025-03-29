from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import EditProfileForm
from .forms import PostForm, CommentForm
from .models import Post, Category, Comment

User = get_user_model()


def get_published_posts():
    return (Post.objects
            .filter(pub_date__lte=timezone.now(),
                    is_published=True,
                    category__is_published=True)
            .select_related('category', 'location')
            .only('id',
                  'title',
                  'pub_date',
                  'category__title',
                  'category__is_published',
                  'is_published',
                  'location',
                  'location__name',
                  'location__is_published',
                  'text',
                  'author__username'))


def index(request):
    posts = get_published_posts()
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    context = {'page_obj': posts}
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.
                             select_related('category', 'location'),
                             pk=post_id)

    if (not post.is_published
            or post.pub_date > timezone.now()
            or not post.category.is_published):
        if request.user != post.author:
            return HttpResponseNotFound()

    form = CommentForm()
    comments = post.comments.all()

    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(Category,
                                 slug=category_slug,
                                 is_published=True)

    filtered_posts = (category.posts
                      .filter(pub_date__lte=timezone.now(), is_published=True)
                      .select_related('category', 'location')
                      .only('id',
                            'title',
                            'pub_date',
                            'category__title',
                            'category__is_published',
                            'is_published',
                            'location',
                            'location__name',
                            'location__is_published',
                            'text',
                            'author__username'))
    paginator = Paginator(filtered_posts, 10)
    page = request.GET.get('page')
    filtered_posts = paginator.get_page(page)

    context = {
        'page_obj': filtered_posts,
        'category': category,
    }
    return render(request, 'blog/category.html', context)


@login_required()
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            if not new_post.pub_date:
                new_post.pub_date = timezone.now()
            new_post.save()
            return redirect('blog:profile', request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


def edit_post(request, post_id):
    post = get_object_or_404(get_published_posts(), pk=post_id)
    if post.author.id != request.user.id:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')

    form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})


def profile(request, username_slug):
    user_profile = get_object_or_404(get_user_model(), username=username_slug)
    posts = user_profile.posts.all()
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    return render(request, 'blog/profile.html',
                  {'profile': user_profile, 'page_obj': posts})


@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', user.username)
    else:
        form = EditProfileForm(instance=user)

    return render(request, 'blog/user.html', {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm()
    return render(request, 'blog/detail.html',
                  {'form': form, 'post': post})


@login_required
def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.post != post:
        return redirect('blog:post_detail', post_id=post_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/comment.html',
                  {'form': form, 'comment': comment})


@login_required
def delete_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.post != post:
        return redirect('blog:post_detail', post_id=post_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(
        request,
        'blog/comment.html',
        {'post': post, 'comment': comment}
    )
