from django.contrib import admin

from .models import Comment, Group, Post


class PostAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group'
    )
    # Добавляем интерфейс для поиска по тексту постов
    search_fields = ('text',)
    # Добавляе возможность изменять поле group в любом посте
    list_editable = ('group',)
    # Добавляем возможность фильтрации по дате
    list_filter = ('pub_date',)
    # Это свойство сработает для всех колонок: где пусто — там будет эта строка
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Comment)
