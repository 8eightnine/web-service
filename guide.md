Инструкция для ИИ: Рефакторинг проекта Django и реализация улучшений (на основе "Лабораторная работа 11.pdf")
Общая цель:
Рефакторинг проекта Django: перевод представлений-функций (FBV) на классы (CBV), внедрение многоразового миксина для оптимизации кода и добавление полнофункциональной постраничной навигации. Все действия должны строго соответствовать документу "Лабораторная работа 11.pdf".

Ожидаемый результат:
Проект Django с обновленной архитектурой представлений, улучшенной структурой кода через миксины и функциональной пагинацией, отвечающей всем критериям задания.

Часть 1: Рефакторинг представлений на основе классов (CBV)
1.1. Общий подход:

Определите назначение каждого представления-функции.

Выберите подходящий CBV из django.views.generic или django.views.

Перенесите логику FBV в атрибуты и методы CBV.

Обновите urls.py, направив маршруты на CBV через .as_view().

1.2. Реализация django.views.View (Пример: функция addpage)

Источник: Стр. 1-3 PDF.

Шаги:

Импортируйте View (from django.views import View).

Создайте класс, наследуемый от View (например, AddPage(View)).

В методе get() реализуйте логику GET-запроса из исходной функции.

В методе post() реализуйте логику POST-запроса из исходной функции.

В urls.py обновите маршрут, используя ИмяКласса.as_view().

1.3. Реализация django.views.generic.TemplateView (Пример: функция index для главной страницы или другие страницы с простым контекстом)

Источник: Стр. 3-5 PDF.

Шаги:

Импортируйте TemplateView (from django.views.generic import TemplateView).

Создайте класс (например, WomenHome(TemplateView)).

Укажите template_name (путь к HTML-шаблону).

Для статического контекста используйте extra_context = {'key': 'value', ...}.

Для динамического контекста переопределите get_context_data(self, **kwargs): вызовите super(), модифицируйте и верните context.

Обновите urls.py.

1.4. Реализация django.views.generic.ListView (Пример: функция index для отображения списков, страницы категорий, страницы тегов)

Источник: Стр. 5-9 PDF.

Для WomenHome (главная страница со списком статей):

Импортируйте ListView (from django.views.generic import ListView).

Унаследуйте WomenHome от ListView.

Укажите model = Women для выборки всех записей или переопределите get_queryset(self) для сложной логики (например, Women.published.all().select_related('cat')).

Установите template_name.

Если имя переменной списка в шаблоне не object_list, установите context_object_name.

Доп. контекст передавайте через extra_context (статика) или get_context_data(**kwargs) (динамика).

Для WomenCategory (страница со списком статей по категории):

Создайте WomenCategory(ListView).

Установите template_name, context_object_name и allow_empty = False (для 404 при пустом списке).

В get_queryset(self) фильтруйте статьи по cat_slug из self.kwargs['cat_slug'].

В get_context_data(**kwargs) установите заголовок, меню и cat_selected.

Обновите urls.py для категорий.

Для TagPostList (страница со списком статей по тегу):

Создайте TagPostList(ListView).

Настройте как WomenCategory, фильтруя по tag_slug.

Обновите urls.py.

1.5. Реализация django.views.generic.DetailView (Пример: функция show_post для отображения одной статьи)

Источник: Стр. 9-11 PDF.

Шаги:

Импортируйте DetailView.

Создайте ShowPost(DetailView).

Установите model, template_name.

Если имя объекта в шаблоне не стандартное, установите context_object_name.

Если имя slug/PK в URL не стандартное, установите slug_url_kwarg / pk_url_kwarg.

В get_context_data(**kwargs) добавьте заголовок и меню.

Для кастомного извлечения объекта (например, только опубликованные) переопределите get_object(self, queryset=None), используя get_object_or_404.

Обновите urls.py.

1.6. Реализация django.views.generic.edit.FormView (Рефакторинг AddPage из View)

Источник: Стр. 12-14 PDF.

Шаги:

Импортируйте FormView (from django.views.generic.edit import FormView).

Унаследуйте AddPage от FormView.

Установите form_class, template_name.

Установите success_url = reverse_lazy('имя_маршрута').

Доп. контекст передавайте через extra_context.

В form_valid(self, form) (вызывается после валидации) сохраните форму (form.save(), если ModelForm) и вызовите super().form_valid(form).

1.7. Реализация django.views.generic.edit.CreateView (Рефакторинг AddPage из FormView)

Источник: Стр. 14-16 PDF.

Шаги:

Импортируйте CreateView.

Унаследуйте AddPage от CreateView.

При использовании ModelForm установите form_class (form_valid обычно не нужен).

Альтернативно: укажите model и fields (список полей или '__all__') для автогенерации формы.

Установите template_name.

Установите success_url или опустите, если в модели есть get_absolute_url().

Доп. контекст передавайте через extra_context.

1.8. Реализация django.views.generic.edit.UpdateView (Создание новой функциональности редактирования)

Источник: Стр. 16-17 PDF.

Шаги:

Импортируйте UpdateView.

Создайте UpdatePage(UpdateView).

Установите model.

Укажите fields для редактирования или form_class.

Установите template_name (можно общий с формой добавления) и success_url.

Доп. контекст (заголовок, меню) передавайте через extra_context.

В urls.py добавьте маршрут с pk или slug для идентификации объекта.

1.9. Реализация django.views.generic.edit.DeleteView (Создание новой функциональности удаления)

Источник: Стр. 17 PDF (указание изучить документацию).

Шаги:

Изучите документацию DeleteView.

Импортируйте DeleteView.

Создайте класс (например, DeletePostView(DeleteView)).

Установите model.

Установите template_name (шаблон подтверждения удаления с формой).

Установите success_url.

Доп. контекст (заголовок) через extra_context или get_context_data.

В urls.py добавьте маршрут с pk или slug.

Часть 2: Реализация многократно используемого миксина (DataMixin)
2.1. Цель: Вынести общий код и данные (например, меню, стандартные элементы контекста) из классов-представлений в отдельный класс-миксин для уменьшения дублирования и улучшения организации кода.

Источник: Стр. 17-21 PDF.

2.2. Создание файла utils.py:

В директории вашего приложения (например, women/) создайте файл utils.py, если он еще не существует.

2.3. Определение класса DataMixin в utils.py:

Перенесите общие данные (например, menu) в utils.py.

Структура DataMixin (согласно стр. 20 PDF):

# women/utils.py
menu = [
    {'title': "О сайте", 'url_name': 'about'},
    {'title': "Добавить статью", 'url_name': 'add_page'},
    {'title': "Обратная связь", 'url_name': 'contact'},
    {'title': "Войти", 'url_name': 'login'}
] # Пример меню из PDF

class DataMixin:
    title_page = None
    extra_context = {} # Используется CBV, которые не переопределяют get_context_data
    paginate_by = 3 # Добавлено для пагинации (стр. 25-26 PDF)

    def __init__(self):
        # Инициализатор для CBV, использующих `extra_context` напрямую (например, CreateView, UpdateView).
        # Наполняет `self.extra_context` для использования базовым CBV.
        if self.title_page:
            self.extra_context['title'] = self.title_page
        if 'menu' not in self.extra_context: # Не перезаписывать, если уже установлено дочерним классом
            self.extra_context['menu'] = menu
        # Можно добавить другие общие элементы в self.extra_context

    def get_mixin_context(self, context, **kwargs):
        # Метод для CBV, переопределяющих `get_context_data` (например, ListView, DetailView).
        # Добавляет общие данные в существующий контекст.

        # Более точное следование PDF стр. 20 (get_mixin_context):
        if self.title_page and 'title' not in kwargs: # Если title не передан в kwargs, используем title_page
             context['title'] = self.title_page

        if 'cat_selected' not in kwargs: # Если cat_selected не передан в kwargs, используем None
            context['cat_selected'] = None

        context['menu'] = menu # Меню всегда из миксина
        context.update(kwargs) # Применяем все переданные kwargs, они могут перезаписать title/cat_selected
                               # если были переданы.
        return context
# Логика `get_mixin_context` (стр. 20 PDF): `title` и `cat_selected` устанавливаются из `kwargs` при наличии,
# иначе `title` берется из `self.title_page`, а `cat_selected` - `None`. `menu` всегда из миксина.
# `context.update(kwargs)` применяет все `kwargs`, которые могут перезаписать предыдущие значения.

2.4. Интеграция DataMixin в классы-представления (views.py):

Импортируйте DataMixin из women.utils.

Добавьте DataMixin первым в список базовых классов CBV: class WomenHome(DataMixin, ListView):.

Для CBV, переопределяющих get_context_data: Вызывайте в них self.get_mixin_context(), передавая текущий контекст и специфичные параметры (например, title, cat_selected).

Пример для WomenHome (стр. 19 PDF):

def get_context_data(self, *, object_list=None, **kwargs):
    context = super().get_context_data(**kwargs) # Получаем контекст от ListView
    # Передаем полученный контекст и специфичные для WomenHome параметры в миксин
    return self.get_mixin_context(context, title='Главная страница', cat_selected=0)

Для CBV, использующих extra_context напрямую (без переопределения get_context_data): Удалите extra_context из класса и установите атрибут title_page. DataMixin.__init__ обработает это.

Часть 3: Реализация постраничной навигации (пагинации)
3.1. Цель: Добавить пагинацию на страницы списков (главная, категории) со следующими требованиями (стр. 28-29 PDF):

Отображение номеров страниц.

Скрытие номеров, если страница всего одна.

Текущий номер страницы – текст, не ссылка.

Ограниченный диапазон номеров слева/справа от текущего (например, по 2).

Условное отображение ссылок "предыдущая"/"следующая".

Источник: Стр. 21-28 PDF.

3.2. Настройка пагинации в представлениях:

В классе DataMixin (см. utils.py выше) уже добавлен атрибут paginate_by = 3 (или другое значение по умолчанию, например, 2 для тестирования диапазона номеров, как на стр. 27 PDF).

Убедитесь, что ваши классы, наследуемые от ListView (например, WomenHome, WomenCategory, TagPostList), также наследуют DataMixin. ListView автоматически использует атрибут paginate_by.

3.3. Модификация шаблонов для отображения пагинации:

PDF предлагает добавить блок {% block navigation %}{% endblock %} в базовый шаблон (base.html) после блока content.

Затем в шаблоне, отображающем список (например, women/index.html), реализуйте этот блок:

{# women/index.html или другой шаблон списка #}
{% block navigation %}
    {% if page_obj.has_other_pages %} {# Требование 2: Не выводить, если всего одна страница #}
    <nav class="list-pages"> {# Используйте классы для стилизации, как в PDF #}
        <ul>
            {# Ссылка на предыдущую страницу #}
            {% if page_obj.has_previous %} {# Требование 5 #}
            <li class="page-num">
                <a href="?page={{ page_obj.previous_page_number }}">&lt;</a> {# &lt; для символа < #}
            </li>
            {% endif %}

            {# Номера страниц #}
            {% for p in paginator.page_range %} {# Требование 1 #}
                {% if page_obj.number == p %}
                    <li class="page-num page-num-selected">{{ p }}</li> {# Требование 3: Текущая страница как текст #}
                {% elif p >= page_obj.number|add:-2 and p <= page_obj.number|add:2 %} {# Требование 4: Ограничение диапазона (по 2 слева/справа) #}
                    <li class="page-num">
                        <a href="?page={{ p }}">{{ p }}</a>
                    </li>
                {% endif %}
            {% endfor %}

            {# Ссылка на следующую страницу #}
            {% if page_obj.has_next %} {# Требование 5 #}
            <li class="page-num">
                <a href="?page={{ page_obj.next_page_number }}">&gt;</a> {# &gt; для символа > #}
            </li>
            {% endif %}
        </ul>
    </nav>
    {% endif %}
{% endblock %}

Примечание: Убедитесь, что фильтр |add:-2 (для диапазона страниц) доступен и корректен.

3.4. Добавление записей в БД для тестирования:

Для проверки пагинации (особенно диапазона номеров) обеспечьте достаточное количество записей в БД (например, 7+ статей при paginate_by = 2 для теста диапазона page_obj.number|add:-2 ... add:2).

3.5. CSS Стилизация:

В CSS (styles.css) определите стили для list-pages, page-num, page-num-selected для корректного вида пагинации.

Часть 4: Финальная проверка
Тщательно протестируйте рефакторинг и новую функциональность (редактирование, удаление, пагинация).

Убедитесь в выполнении всех пунктов задания (стр. 28-29 PDF).

Проверьте консоли браузера и Django на ошибки.

Проверьте корректность навигации, отображения данных и работы форм.

Протестируйте пагинацию на разных страницах и с разным числом элементов.