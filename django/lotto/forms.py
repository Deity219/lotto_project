# 입력 검증을 한 곳에 모아서 깔끔하게 처리
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class ManualTicketForm(forms.Form):
    n1 = forms.IntegerField(min_value=1, max_value=45)
    n2 = forms.IntegerField(min_value=1, max_value=45)
    n3 = forms.IntegerField(min_value=1, max_value=45)
    n4 = forms.IntegerField(min_value=1, max_value=45)
    n5 = forms.IntegerField(min_value=1, max_value=45)
    n6 = forms.IntegerField(min_value=1, max_value=45)

    def clean(self):
        cleaned = super().clean()
        nums = [cleaned.get(f'n{i}') for i in range(1, 7)]
        if None in nums:
            return cleaned
        if len(set(nums)) != 6:
            raise forms.ValidationError('6개 번호는 모두 달라야 합니다.')
        return cleaned


class AutoTicketForm(forms.Form):
    count = forms.IntegerField(min_value=1, max_value=5, initial=1,
                               label='자동 구매 매수')
    
class KoreanUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username',)
        labels = {'username': '아이디'}
        help_texts = {'username': '150자 이하의 영문, 숫자, @/./+/-/_ 만 사용 가능합니다.'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = '비밀번호'
        self.fields['password1'].help_text = (
            '비밀번호는 최소 8자 이상이어야 하며, '
            '아이디와 너무 비슷하거나 너무 단순하면 거부됩니다.'
        )
        self.fields['password2'].label = '비밀번호 확인'
        self.fields['password2'].help_text = '확인을 위해 동일한 비밀번호를 한 번 더 입력하세요.'
        # 모든 필드 에러 메시지 한글화
        for field in self.fields.values():
            field.error_messages = {
                'required': '이 항목은 필수입니다.',
                'unique': '이미 사용 중입니다.',
            }