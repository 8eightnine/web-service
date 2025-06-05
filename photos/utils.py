class DataMixin:
    """Mixin class to provide common context data across multiple CBVs"""
    title_page = None
    extra_context = {}
    paginate_by = 6

    def __init__(self):
        if not hasattr(self, 'extra_context') or not self.extra_context:
            self.extra_context = {}

        if self.title_page:
            self.extra_context['title'] = self.title_page

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
        context.update(self.extra_context)

        context.update(kwargs)

        return context
