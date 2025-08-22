from time import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status, generics
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Max
from .models import Video, VideoCategory
from .serializers import VideoSerializer, VideoCategorySerializer
import re
import logging
from django.core.files.storage import FileSystemStorage
from .models import Article, Category, CustomUser, Writer
from .serializers import ArticleSerializer, CategorySerializer, LoginSerializer, WriterSerializer

logger = logging.getLogger(__name__)

# backend/api/permissions.py
from rest_framework.permissions import BasePermission, IsAuthenticated

class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Allows unauthenticated users to perform read operations (GET),
    but requires authentication for write operations (POST, PUT, DELETE).
    """
    def has_permission(self, request, view):
        # Allow GET requests without authentication
        if request.method == 'GET':
            return True
        # Require authentication for other methods
        return IsAuthenticated().has_permission(request, view)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            login(request, user)
            try:
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                logger.info(f"Login successful for user: {user.username}, is_superuser: {user.is_superuser}")
                return Response({
                    'user': {
                        'username': user.username,
                        'role': getattr(user, 'role', 'admin' if user.is_superuser else 'viewer'),
                        'is_superuser': user.is_superuser
                    },
                    'token': access_token,
                    'refresh': str(refresh),
                    'message': 'Login successful'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error generating token for user {user.username}: {str(e)}")
                return Response({'error': 'Token generation failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.warning(f"Login failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckAuthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        if request.user.is_authenticated:
            logger.info(f"User found: {request.user.username}")
            return Response({
                'isAuthenticated': True,
                'user': {
                    'username': request.user.username,
                    'role': getattr(request.user, 'role', 'admin' if request.user.is_superuser else 'viewer'),
                    'is_superuser': request.user.is_superuser
                }
            }, status=status.HTTP_200_OK)
        logger.warning("No authenticated user found")
        return Response({
            'isAuthenticated': False,
            'error': 'No authenticated user'
        }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            logout(request)
            logger.info("User logged out successfully")
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return Response({'error': 'Logout failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WriterListCreateView(generics.ListCreateAPIView):
    queryset = Writer.objects.all()
    serializer_class = WriterSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        serializer.save()

class WriterDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Writer.objects.all()
    serializer_class = WriterSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_authenticators(self):
        # Bypass JWT authentication for GET requests
        if self.request.method == 'GET':
            return []
        return [JWTAuthentication()]

    def perform_create(self, serializer):
        max_order = Category.objects.all().aggregate(Max('order'))['order__max'] or 0
        serializer.save(order=max_order + 1)

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def perform_destroy(self, instance):
        if instance.articlesCount > 0:
            raise serializers.ValidationError("Cannot delete category with associated articles.")
        instance.delete()
        
class ArticleListCreateView(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # Use custom permission class

    def get_authenticators(self):
        # Bypass JWT authentication for GET requests
        if self.request.method == 'GET':
            return []
        return [JWTAuthentication()]  # Use rest_framework_simplejwt.authentication.JWTAuthentication

    def perform_create(self, serializer):
        try:
            serializer.save()
            logger.info(f"Article created successfully by user: {self.request.user.username}")
        except Exception as e:
            logger.error(f"Article creation failed: {str(e)}")
            raise

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except serializers.ValidationError as e:
            logger.warning(f"Article validation failed: {e.detail}")
            return Response({'detail': e.detail}, status=status.HTTP_400_BAD_REQUEST)

class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # Use custom permission class

    def get_authenticators(self):
        # Bypass JWT authentication for GET requests
        if self.request.method == 'GET':
            return []
        return [JWTAuthentication()]  # Use rest_framework_simplejwt.authentication.JWTAuthentication

    def perform_update(self, serializer):
        try:
            serializer.save()
            logger.info(f"Article {serializer.instance.id} updated by user: {self.request.user.username}")
        except Exception as e:
            logger.error(f"Article update failed: {str(e)}")
            raise

    def perform_destroy(self, instance):
        try:
            instance.category.articlesCount -= 1
            instance.category.save()
            instance.author.articles_count -= 1
            instance.author.save()
            instance.delete()
            logger.info(f"Article {instance.id} deleted by user: {self.request.user.username}")
        except Exception as e:
            logger.error(f"Article deletion failed: {str(e)}")
            raise
        
class ArticleStatsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        try:
            total = Article.objects.count()
            published = Article.objects.filter(status='published').count()
            drafts = Article.objects.filter(status='draft').count()
            scheduled = Article.objects.filter(status='scheduled').count()
            return Response({
                'total': total,
                'published': published,
                'drafts': drafts,
                'scheduled': scheduled,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching article stats: {str(e)}")
            return Response({'detail': 'Failed to fetch stats'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UploadView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def sanitize_filename(self, filename):
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('._')
        return filename

    def post(self, request):
        try:
            if 'file' not in request.FILES:
                logger.warning("No file provided in upload request")
                return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

            file = request.FILES['file']
            if not file.content_type.startswith('image/'):
                logger.warning(f"Invalid file type uploaded: {file.content_type}")
                return Response({'detail': 'Only image files are allowed.'}, status=status.HTTP_400_BAD_REQUEST)
            if file.size > 5 * 1024 * 1024:
                logger.warning(f"File size exceeds limit: {file.size} bytes")
                return Response({'detail': 'File size exceeds 5MB limit.'}, status=status.HTTP_400_BAD_REQUEST)

            original_filename = file.name
            sanitized_filename = self.sanitize_filename(original_filename)
            logger.info(f"Original filename: {original_filename}, Sanitized filename: {sanitized_filename}")

            fs = FileSystemStorage(location='media/uploads/')
            filename = fs.save(sanitized_filename, file)
            file_url = f"/media/uploads/{filename}"
            logger.info(f"File uploaded successfully: {filename}")
            return Response({'url': file_url}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return Response({'detail': f'File upload failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)




class VideoCategoryListCreateView(generics.ListCreateAPIView):
    queryset = VideoCategory.objects.all()
    serializer_class = VideoCategorySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

class VideoListCreateView(generics.ListCreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user)

class VideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

class VideoLiveView(generics.UpdateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def patch(self, request, *args, **kwargs):
        video = self.get_object()
        if 'is_live' in request.data and request.data['is_live'] is True:
            video.is_live = True
            video.live_start_time = timezone.now()
            video.status = 'live'
            video.save()
            return Response({'detail': 'Video is now live.'}, status=status.HTTP_200_OK)
        elif 'is_live' in request.data and request.data['is_live'] is False:
            video.is_live = False
            video.live_end_time = timezone.now()
            video.status = 'archived'
            video.save()
            return Response({'detail': 'Video live stream ended and archived.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'No valid action.'}, status=status.HTTP_400_BAD_REQUEST)


class VideoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def sanitize_filename(self, filename):
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('._')
        return filename

    def post(self, request):
        try:
            if 'file' not in request.FILES:
                logger.warning("No file provided in video upload request")
                return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

            file = request.FILES['file']

            # Check if the file is a video
            if not file.content_type.startswith('video/'):
                logger.warning(f"Invalid file type uploaded: {file.content_type}")
                return Response({'detail': 'Only video files are allowed.'}, status=status.HTTP_400_BAD_REQUEST)

            # 500MB size limit for videos
            if file.size > 500 * 1024 * 1024:
                logger.warning(f"Video file size exceeds limit: {file.size} bytes")
                return Response({'detail': 'Video file size exceeds 500MB limit.'}, status=status.HTTP_400_BAD_REQUEST)

            original_filename = file.name
            sanitized_filename = self.sanitize_filename(original_filename)
            logger.info(f"Original filename: {original_filename}, Sanitized filename: {sanitized_filename}")

            # Save videos to 'media/videos/'
            fs = FileSystemStorage(location='media/videos/')
            filename = fs.save(sanitized_filename, file)
            file_url = f"/media/videos/{filename}"
            logger.info(f"Video uploaded successfully: {filename}")
            return Response({'url': file_url}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error uploading video: {str(e)}")
            return Response({'detail': f'Video upload failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

