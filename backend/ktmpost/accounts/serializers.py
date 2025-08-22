from rest_framework import serializers
from django.contrib.auth import authenticate
import logging
from .models import CustomUser, Writer, Category, Article
from rest_framework import serializers
from .models import Video, VideoCategory

logger = logging.getLogger(__name__)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            logger.info(f"User {data['username']} authenticated successfully")
            return user
        logger.warning(f"Authentication failed for username: {data['username']}")
        raise serializers.ValidationError("Invalid credentials")

class WriterSerializer(serializers.ModelSerializer):
    expertise = serializers.ListField(child=serializers.CharField(), required=False)
    social_links = serializers.DictField(child=serializers.CharField(allow_blank=True), required=False)

    class Meta:
        model = Writer
        fields = [
            'id', 'name', 'email', 'phone', 'role', 'department', 'expertise',
            'bio', 'location', 'social_links', 'avatar', 'join_date',
            'articles_count', 'status'
        ]
        read_only_fields = ['id', 'join_date', 'articles_count']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'nameEnglish', 'description', 'color', 'icon',
            'subcategories', 'seoTitle', 'seoDescription', 'isActive',
            'articlesCount', 'order', 'createdAt'
        ]
        read_only_fields = ['id', 'createdAt', 'articlesCount']

class ArticleSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    gallery = serializers.ListField(child=serializers.DictField(), required=False)
    featuredImage = serializers.URLField(allow_null=True, required=False)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'excerpt', 'content', 'category', 'subcategory', 'author',
            'featuredImage', 'gallery', 'tags', 'status', 'isFeatured', 'isHot',
            'isTrending', 'isBreaking', 'publishDate', 'publishTime', 'seoTitle',
            'seoDescription', 'seoKeywords', 'readTime', 'views', 'createdAt', 'updatedAt'
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt', 'readTime', 'views']

    def validate(self, data):
        if data.get('subcategory') and data.get('category'):
            if data['subcategory'] not in data['category'].subcategories:
                raise serializers.ValidationError({
                    'subcategory': f"Subcategory '{data['subcategory']}' is not valid for category '{data['category'].name}'."
                })
        if not data.get('title'):
            raise serializers.ValidationError({'title': 'Title is required.'})
        if not data.get('excerpt'):
            raise serializers.ValidationError({'excerpt': 'Excerpt is required.'})
        if not data.get('content'):
            raise serializers.ValidationError({'content': 'Content is required.'})
        if not data.get('category'):
            raise serializers.ValidationError({'category': 'Category is required.'})
        if not data.get('author'):
            raise serializers.ValidationError({'author': 'Author is required.'})
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['category'] = {
            'id': instance.category.id,
            'name': instance.category.name,
            'subcategories': instance.category.subcategories
        }
        representation['author'] = {
            'id': instance.author.id,
            'name': instance.author.name
        }
        return representation


class VideoCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoCategory
        fields = ['id', 'name', 'description', 'isActive', 'createdAt']

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'video_type', 'video_file', 'thumbnail',
            'platform', 'platform_url', 'status', 'is_live', 'live_start_time',
            'live_end_time', 'category', 'uploader', 'views', 'createdAt', 'updatedAt'
        ]
        read_only_fields = ['id', 'uploader', 'views', 'createdAt', 'updatedAt']

    def validate(self, data):
        if data.get('is_live') and not data.get('live_start_time'):
            raise serializers.ValidationError({'live_start_time': 'Live start time is required for live videos.'})
        if data.get('platform') in ['youtube', 'facebook'] and not data.get('platform_url'):
            raise serializers.ValidationError({'platform_url': 'Platform URL is required for YouTube/Facebook videos.'})
        return data
