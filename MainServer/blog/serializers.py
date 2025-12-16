from rest_framework import serializers
from .models import Post, AnalysisReport

class PostSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True, required=False)

    class Meta:
        model = Post
        fields = ('author', 'title', 'text', 'created_date', 'published_date', 'image', 'confidence', 'bbox')

class AnalysisReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisReport
        fields = ['summary', 'plot_urls', 'people_data'] # Added people_data