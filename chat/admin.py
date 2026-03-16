from django.contrib import admin
from django.utils import timezone
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'content', 'created_at', 'is_read')
    fields = ('sender', 'content', 'is_read', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'participant_count', 'last_message_preview', 'message_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('participants__username',)
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('participants',)
    inlines = [MessageInline]
    
    fieldsets = (
        ('Conversation Info', {
            'fields': ('participants',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    def last_message_preview(self, obj):
        last_msg = obj.messages.first()
        if last_msg:
            return f"{last_msg.sender.username}: {last_msg.content[:50]}..."
        return "No messages"
    last_message_preview.short_description = 'Last Message'
    
    actions = ['mark_all_read', 'delete_old_conversations']
    
    def mark_all_read(self, request, queryset):
        for conversation in queryset:
            conversation.messages.filter(is_read=False).update(is_read=True)
        self.message_user(request, f"Marked all messages as read in {queryset.count()} conversations.")
    mark_all_read.short_description = "Mark all messages as read"
    
    def delete_old_conversations(self, request, queryset):
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        old_convs = queryset.filter(updated_at__lt=thirty_days_ago)
        count = old_convs.count()
        old_convs.delete()
        self.message_user(request, f"Deleted {count} old conversations.")
    delete_old_conversations.short_description = "Delete conversations older than 30 days"

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation_id', 'sender', 'content_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at', 'sender')
    search_fields = ('content', 'sender__username', 'conversation__id')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Message Info', {
            'fields': ('conversation', 'sender', 'content')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
    
    def content_preview(self, obj):
        return obj.content[:75] + "..." if len(obj.content) > 75 else obj.content
    content_preview.short_description = 'Content'
    
    def conversation_id(self, obj):
        return obj.conversation.id
    conversation_id.short_description = 'Conversation ID'
    conversation_id.admin_order_field = 'conversation__id'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} messages marked as read.")
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} messages marked as unread.")
    mark_as_unread.short_description = "Mark selected messages as unread"