from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

class Writer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    expertise = models.JSONField(default=list, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    social_links = models.JSONField(default=dict, blank=True)
    avatar = models.URLField(blank=True)
    join_date = models.DateField(auto_now_add=True)
    articles_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='active', choices=[('active', 'Active'), ('inactive', 'Inactive')])

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=255)
    nameEnglish = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')
    icon = models.CharField(max_length=10, blank=True)
    subcategories = models.JSONField(default=list, blank=True)
    seoTitle = models.CharField(max_length=255, blank=True)
    seoDescription = models.TextField(blank=True)
    isActive = models.BooleanField(default=True)
    articlesCount = models.IntegerField(default=0)
    order = models.IntegerField(default=0)
    createdAt = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

class Article(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
    )
    title = models.CharField(max_length=255)
    excerpt = models.TextField()
    content = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    subcategory = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey(Writer, on_delete=models.CASCADE, related_name='articles')
    featuredImage = models.URLField(blank=True)
    gallery = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    isFeatured = models.BooleanField(default=False)
    isHot = models.BooleanField(default=False)
    isTrending = models.BooleanField(default=False)
    isBreaking = models.BooleanField(default=False)
    publishDate = models.DateField(default=timezone.now)
    publishTime = models.TimeField(default=timezone.now)
    seoTitle = models.CharField(max_length=255, blank=True)
    seoDescription = models.TextField(blank=True)
    seoKeywords = models.CharField(max_length=255, blank=True)
    readTime = models.IntegerField(default=0)
    views = models.PositiveIntegerField(default=0)  # New field for views
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def clean(self):
        if self.subcategory and self.category:
            if self.subcategory not in self.category.subcategories:
                raise ValidationError(f"Subcategory '{self.subcategory}' is not valid for category '{self.category.name}'.")

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.category.articlesCount += 1
            self.category.save()
            self.author.articles_count += 1
            self.author.save()
        else:
            old_article = Article.objects.get(pk=self.pk)
            if old_article.category_id != self.category_id:
                old_article.category.articlesCount -= 1
                old_article.category.save()
                self.category.articlesCount += 1
                self.category.save()
            if old_article.author_id != self.author_id:
                old_article.author.articles_count -= 1
                old_article.author.save()
                self.author.articles_count += 1
                self.author.save()

        if self.isFeatured:
            featured_articles = Article.objects.filter(isFeatured=True).exclude(pk=self.pk).order_by('-updatedAt')
            if featured_articles.count() >= 3:
                oldest_featured = featured_articles.last()
                if oldest_featured:
                    oldest_featured.isFeatured = False
                    oldest_featured.save()

        super().save(*args, **kwargs)



class VideoCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    isActive = models.BooleanField(default=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Video(models.Model):
    VIDEO_TYPE_CHOICES = (
        ('news', 'News'),
        ('broadcast', 'Broadcast'),
        ('interview', 'Interview'),
        ('documentary', 'Documentary'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('live', 'Live'),
        ('archived', 'Archived'),
    )
    PLATFORM_CHOICES = (
        ('youtube', 'YouTube'),
        ('facebook', 'Facebook'),
        ('custom', 'Custom'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_type = models.CharField(max_length=20, choices=VIDEO_TYPE_CHOICES, default='news')
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    thumbnail = models.URLField(blank=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='custom')
    platform_url = models.URLField(blank=True)  # For YouTube/Facebook live URLs
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_live = models.BooleanField(default=False)
    live_start_time = models.DateTimeField(blank=True, null=True)
    live_end_time = models.DateTimeField(blank=True, null=True)
    category = models.ForeignKey(VideoCategory, on_delete=models.SET_NULL, null=True, blank=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='videos')
    views = models.PositiveIntegerField(default=0)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.is_live and self.live_end_time and self.live_end_time < timezone.now():
            self.status = 'archived'
            self.is_live = False
        super().save(*args, **kwargs)
