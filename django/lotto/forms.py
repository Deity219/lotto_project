# 입력 검증을 한 곳에 모아서 깔끔하게 처리
from django import forms


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