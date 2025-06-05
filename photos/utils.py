from django.urls import reverse_lazy


class DataMixin:
    """Mixin class to provide common context data across multiple CBVs"""
    title_page = None
    extra_context = {}
    paginate_by = 6  # Default pagination

    def __init__(self):
        # Initialize extra_context if not already set
        if not hasattr(self, 'extra_context') or not self.extra_context:
            self.extra_context = {}

        # Add title to extra_context if title_page is set
        if self.title_page:
            self.extra_context['title'] = self.title_page

        # Add common menu items
        self.extra_context.update({
            'menu': [
                {
                    'title': 'Все фото',
                    'url_name': 'photo_list'
                },
                {
                    'title': 'Загрузить фото',
                    'url_name': 'upload_photo'
                },
                {
                    'title': 'Теги',
                    'url_name': 'tag_list'
                },
                {
                    'title': 'Статистика',
                    'url_name': 'stats'
                },
            ]
        })

    def get_mixin_context(self, context, **kwargs):
        """
        Aggregate context from mixin's extra_context and passed kwargs
        """
        # Start with the base context
        context.update(self.extra_context)

        # Add any additional context passed as kwargs
        context.update(kwargs)

        return context
