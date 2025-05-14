from django import forms

class YouTubeDownloadForm(forms.Form):
    url = forms.URLField(
        label='YouTube URL',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập URL video YouTube',
            'id': 'youtube-url'
        })
    )
    format_choice = forms.ChoiceField(
        label='Định dạng',
        choices=[('mp4', 'MP4 (Video)'), ('mp3', 'MP3 (Audio)')],
        widget=forms.RadioSelect(attrs={'class': 'format-choice'}),
        initial='mp4'
    )
    
    # Bonus feature: Video quality (optional)
    quality = forms.ChoiceField(
        label='Chất lượng',
        choices=[
            ('highest', 'Cao nhất'),
            ('medium', 'Trung bình'),
            ('lowest', 'Thấp nhất')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='highest',
        required=False
    )
