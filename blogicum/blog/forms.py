from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title',
                  'text',
                  'pub_date',
                  'category',
                  'location',
                  'image']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
