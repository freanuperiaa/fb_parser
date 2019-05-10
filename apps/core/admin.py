from django.contrib import admin
from django.db.models import Count

from .models import FacebookGroup, Post, Comment


admin.site.register(Comment)


@admin.register(FacebookGroup)
class FacebookGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'url']
    

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'url',
        'group',
        'author',
        'total_reacts',
        'no_comments',
        'desc'
    ]

    def no_comments(self, obj):
        return obj.comments.count()

    def desc(self, obj):
        str = obj.description
        return str[:50]
