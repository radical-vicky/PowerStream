from django.contrib import admin
from .models import Comment, CommentLike, Share, Tip

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'content_preview', 'likes_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'content')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'created_at')
    list_filter = ('created_at',)

@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'platform', 'created_at')
    list_filter = ('platform', 'created_at')

@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'video', 'amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('sender__username', 'recipient__username')