from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from .models import FAQ
from .models import ChatSession, ChatMessage, UnansweredQuestion

admin.site.register(ChatSession)
admin.site.register(ChatMessage)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category')
    list_filter = ('category',)
    search_fields = ('question', 'keywords', 'answer')

    def get_changeform_initial_data(self, request):
        """
        Lets the 'Convert to FAQ' link on the Unanswered Questions page
        pre-fill the question text on the FAQ add form.
        """
        initial = super().get_changeform_initial_data(request)
        question = request.GET.get('question')
        if question:
            initial['question'] = question
        return initial


@admin.register(UnansweredQuestion)
class UnansweredQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'question', 'asked_by', 'times_asked',
        'is_resolved', 'last_asked_at', 'convert_to_faq_link',
    )
    list_filter = ('is_resolved',)
    search_fields = ('question',)
    ordering = ('is_resolved', '-last_asked_at')
    actions = ['mark_resolved', 'mark_unresolved']

    def convert_to_faq_link(self, obj):
        url = reverse('admin:campusbot_faq_add') + '?' + urlencode({'question': obj.question})
        return format_html('<a class="button" href="{}">Add to FAQ</a>', url)
    convert_to_faq_link.short_description = 'Convert to FAQ'

    def mark_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f"{updated} question(s) marked as resolved.")
    mark_resolved.short_description = "Mark selected questions as resolved"

    def mark_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False)
        self.message_user(request, f"{updated} question(s) marked as unresolved.")
    mark_unresolved.short_description = "Mark selected questions as unresolved"














