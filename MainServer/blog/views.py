from rest_framework import viewsets
from .models import AnalysisReport, Post
from .serializers import PostSerializer, AnalysisReportSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.utils import timezone
import datetime

import os
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

class BlogImages(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_date')
    serializer_class = PostSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        queryset = Post.objects.all().order_by('-created_date')
        date_str = self.request.query_params.get('date', None)
        
        if date_str is not None:
            try:
                target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(created_date__date=target_date)
            except ValueError:
                pass
        
        return queryset

class AnalysisImageUploadView(APIView):
    """
    Allows the Analysis Module to upload generated plots (PNGs).
    """
    permission_classes = [AllowAny] # Or restrict to internal IP/Token
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        if 'file' not in request.data:
            return Response({"error": "No file provided"}, status=400)

        file_obj = request.data['file']
        
        # Generate unique filename
        ext = file_obj.name.split('.')[-1]
        filename = f"analysis_plot_{uuid.uuid4().hex[:8]}.{ext}"
        
        # Save manually to media/analysis directory
        save_path = os.path.join('analysis', filename)
        saved_path = default_storage.save(save_path, ContentFile(file_obj.read()))
        
        # Construct full URL
        # NOTE: In production, ensure MEDIA_URL is configured correctly
        full_url = request.build_absolute_uri(settings.MEDIA_URL + saved_path)
        
        return Response({"url": full_url}, status=201)
    
class AnalysisView(APIView):
    # GET: Protected (Android App needs token)
    # POST: AllowAny (or use internal IP check) so local script can push data
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        latest_report = AnalysisReport.objects.first()
        if not latest_report:
            return Response({"summary": "No analysis generated yet.", "plot_urls": [], "people_data": []})
        
        urls = latest_report.plot_urls.split(',') if latest_report.plot_urls else []
        
        # Parse the JSON string back to a list object for the response
        try:
            people_groups = json.loads(latest_report.people_data)
        except:
            people_groups = []

        return Response({
            "summary": latest_report.summary,
            "plot_urls": urls,
            "people_data": people_groups # Return structured list
        })

    def post(self, request):
        summary = request.data.get('summary')
        plots = request.data.get('plot_urls', []) 
        
        # Expecting a List of Dicts
        people_groups = request.data.get('people_data', []) 
        
        # Serialize lists to string for storage
        plot_string = ",".join(plots)
        people_string = json.dumps(people_groups)
        
        report = AnalysisReport.objects.create(
            summary=summary, 
            plot_urls=plot_string, 
            people_data=people_string
        )
        return Response({"status": "Report Saved", "id": report.id})
    
@login_required
def web_index(request):
    """
    Main Dashboard: Mirrors the Android Main Activity.
    Displays a list of detected objects with images and metadata.
    """
    posts = Post.objects.all().order_by('-created_date')
    return render(request, 'index.html', {'posts': posts})

@login_required
def web_report(request):
    """
    Analysis Page: Mirrors the Android Analysis Activity.
    Displays summary, general plots, and grouped person identities.
    """
    report = AnalysisReport.objects.first() # Get latest report
    
    context = {
        'summary': "No analysis generated yet.",
        'plots': [],
        'people_groups': []
    }

    if report:
        context['summary'] = report.summary
        
        # Parse Plot URLs (stored as CSV string)
        if report.plot_urls:
            context['plots'] = report.plot_urls.split(',')
        
        # Parse People Groups (stored as JSON string)
        if report.people_data:
            try:
                context['people_groups'] = json.loads(report.people_data)
            except json.JSONDecodeError:
                context['people_groups'] = []

    return render(request, 'analysis.html', context)