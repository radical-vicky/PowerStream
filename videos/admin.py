from django.contrib import admin
from .models import Category, Video, Like

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'privacy', 'likes_count', 'comments_count', 'created_at')
    list_filter = ('privacy', 'category', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('likes_count', 'comments_count', 'shares_count')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'user', 'category')
        }),
        ('Media', {
            'fields': ('thumbnail', 'video_file', 'duration')
        }),
        ('Settings', {
            'fields': ('privacy', 'allow_comments', 'allow_ratings')
        }),
        ('Stats', {
            'fields': ('likes_count', 'comments_count', 'shares_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Like)