from django.contrib import admin
from .models import Background

@admin.register(Background)
class BackgroundAdmin(admin.ModelAdmin):
    list_display = ('name', 'bg_type', 'is_active', 'created_at')
    list_filter = ('bg_type', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'bg_type', 'is_active')
        }),
        ('Background Content', {
            'fields': ('color', 'image', 'video'),
            'description': 'Fill based on selected background type'
        }),
        ('Color Customization', {
            'fields': (
                'card_bg_color', 'hover_bg_color', 
                'text_color', 'text_secondary_color',
                'border_color', 'accent_color', 'accent_hover_color'
            ),
        }),
        ('Overlay Settings', {
            'fields': ('overlay_opacity', 'navbar_opacity'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # If this background is set to active, deactivate all others
        if obj.is_active:
            Background.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)