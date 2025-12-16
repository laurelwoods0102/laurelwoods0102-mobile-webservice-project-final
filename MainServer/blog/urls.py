from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from . import views
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'Post', views.BlogImages)

urlpatterns = [
    url(r'^api_root/', include(router.urls)),
    url(r'^api_root/analysis/', views.AnalysisView.as_view()),
    url(r'^api_root/upload_plot/', views.AnalysisImageUploadView.as_view()),

    url(r'^login/$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    url(r'^$', views.web_index, name='index'),       # Main View
    url(r'^report/$', views.web_report, name='report'), # Analysis Page
]
