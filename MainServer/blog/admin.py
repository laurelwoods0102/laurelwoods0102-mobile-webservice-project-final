from django.contrib import admin
from .models import Post, AnalysisReport

admin.site.register(Post)

# Register the AnalysisReport model to see Re-ID results
@admin.register(AnalysisReport)
class AnalysisReportAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'short_summary')
    readonly_fields = ('created_at',)
    
    # Helper to show a snippet of the summary in the list view
    def short_summary(self, obj):
        return obj.summary[:100] + "..." if obj.summary else "No Summary"