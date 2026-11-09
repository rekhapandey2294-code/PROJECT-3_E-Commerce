from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(5, '★★★★★ (5 - Excellent)'), (4, '★★★★☆ (4 - Good)'), (3, '★★★☆☆ (3 - Average)'), (2, '★★☆☆☆ (2 - Poor)'), (1, '★☆☆☆☆ (1 - Terrible)')],
                attrs={'class': 'form-select'}
            ),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Summarize your experience'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'What did you like or dislike about this product?'}),
        }
