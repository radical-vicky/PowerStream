from django.contrib import admin
from .models import Channel

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'subscriber_count', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'is_private', 'created_at')
    search_fields = ('name', 'description', 'owner__username')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'description', 'owner')
        }),
        ('Media', {
            'fields': ('avatar', 'cover_image')
        }),
        ('Settings', {
            'fields': ('is_private', 'is_verified')
        }),
        ('Stats', {
            'fields': ('total_videos', 'total_views')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def subscriber_count(self, obj):
        return obj.subscribers.count()
    subscriber_count.short_description = 'Subscribers'