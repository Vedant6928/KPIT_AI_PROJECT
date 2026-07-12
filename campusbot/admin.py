from django.contrib import admin
from .models import Register_details, FAQ

admin.site.register(Register_details)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category')
    list_filter = ('category',)
    search_fields = ('question', 'keywords', 'answer')














