from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q, Count
from .models import Post, Category, Comment, Like, Bookmark, ContactMessage
from .forms import CommentForm, ContactForm, SearchForm

def home(request):
    posts = Post.objects.filter(is_published=True).annotate(
        like_count=Count('likes'),
        comment_count=Count('comments')
    )
    
    # Search functionality
    search_form = SearchForm(request.GET or None)
    query = request.GET.get('query')
    
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    # Popular posts (most viewed)
    popular_posts = Post.objects.filter(is_published=True).order_by('-views')[:5]
    
    # Pagination
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'home.html', {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'search_form': search_form,
        'query': query,
        'popular_posts': popular_posts
    })

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    
    # Increment view count
    post.increment_views()
    
    # Check if user liked/bookmarked
    user_liked = False
    user_bookmarked = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(post=post, user=request.user).exists()
        user_bookmarked = Bookmark.objects.filter(post=post, user=request.user).exists()
    
    if request.method == 'POST':
        if 'comment' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.post = post
                comment.save()
                messages.success(request, 'Your comment has been submitted for review!')
                return redirect('post_detail', slug=post.slug)
        elif 'contact' in request.POST:
            contact_form = ContactForm(request.POST)
            if contact_form.is_valid():
                contact_form.save()
                messages.success(request, 'Your message has been sent!')
                return redirect('post_detail', slug=post.slug)
    else:
        form = CommentForm()
        contact_form = ContactForm()
    
    return render(request, 'post_detail.html', {
        'post': post,
        'form': form,
        'contact_form': contact_form,
        'categories': Category.objects.all(),
        'user_liked': user_liked,
        'user_bookmarked': user_bookmarked,
        'like_count': post.likes.count(),
        'bookmark_count': post.bookmarks.count()
    })

def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category, is_published=True)
    
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'category.html', {
        'category': category,
        'page_obj': page_obj,
        'categories': Category.objects.all()
    })

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    
    if not created:
        like.delete()
        messages.info(request, 'Post unliked!')
    else:
        messages.success(request, 'Post liked!')
    
    return redirect('post_detail', slug=post.slug)

@login_required
def bookmark_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    bookmark, created = Bookmark.objects.get_or_create(post=post, user=request.user)
    
    if not created:
        bookmark.delete()
        messages.info(request, 'Post removed from bookmarks!')
    else:
        messages.success(request, 'Post bookmarked!')
    
    return redirect('post_detail', slug=post.slug)

@login_required
def my_bookmarks(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('post')
    return render(request, 'bookmarks.html', {
        'bookmarks': bookmarks,
        'categories': Category.objects.all()
    })

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {
        'form': form,
        'categories': Category.objects.all()
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})