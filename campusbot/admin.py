from django.contrib import admin
from .models import  FAQ
from .models import ChatSession, ChatMessage

admin.site.register(ChatSession)
admin.site.register(ChatMessage)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category')
    list_filter = ('category',)
    search_fields = ('question', 'keywords', 'answer')














