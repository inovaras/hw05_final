from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст', 'group': 'Группа'}
        help_texts = {
            'text': 'Добавьте новую запись',
            'group': 'Выберете группу',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {'text': 'Оставьте комментарий'}
