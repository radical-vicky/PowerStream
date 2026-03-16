from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Follow

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Info', {'fields': ('bio', 'avatar', 'cover_image', 'location', 'website', 'is_verified')}),
        ('Stats', {'fields': ('total_views', 'total_likes', 'total_followers', 'total_following')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Follow)