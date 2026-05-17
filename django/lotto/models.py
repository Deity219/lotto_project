# lotto/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random


class DrawRound(models.Model):
    # 회차 모델: 회차 번호, 추첨일, 당첨번호 6개 + 보너스번호, 추첨완료 여부, 생성일
    round_no = models.IntegerField('회차', unique=True)
    draw_date = models.DateTimeField('추첨일', null=True, blank=True)
    n1 = models.IntegerField(null=True, blank=True)
    n2 = models.IntegerField(null=True, blank=True)
    n3 = models.IntegerField(null=True, blank=True)
    n4 = models.IntegerField(null=True, blank=True)
    n5 = models.IntegerField(null=True, blank=True)
    n6 = models.IntegerField(null=True, blank=True)
    bonus = models.IntegerField('보너스', null=True, blank=True)
    is_drawn = models.BooleanField('추첨완료', default=False)
    created_at = models.DateTimeField('회차 생성일', default=timezone.now)

    class Meta:
        ordering = ['-round_no']

    def __str__(self):
        return f"{self.round_no}회차"

    def winning_numbers(self):
        if not self.is_drawn:
            return None
        return sorted([self.n1, self.n2, self.n3, self.n4, self.n5, self.n6])

    def execute_draw(self):
        # 1~45 중 6개 + 보너스 1개 무작위 추첨
        picked = random.sample(range(1, 46), 7)
        nums = sorted(picked[:6])
        self.n1, self.n2, self.n3, self.n4, self.n5, self.n6 = nums
        self.bonus = picked[6]
        self.draw_date = timezone.now()
        self.is_drawn = True
        self.save()


class Ticket(models.Model):
    # 복권 한 장, 강의의 Choice 모델처럼 ForeignKey 연결
    PICK_MANUAL = 'M'
    PICK_AUTO = 'A'
    PICK_CHOICES = [(PICK_MANUAL, '수동'), (PICK_AUTO, '자동')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='구매자')
    draw_round = models.ForeignKey(DrawRound, on_delete=models.CASCADE,
                                    related_name='tickets', verbose_name='회차')
    n1 = models.IntegerField()
    n2 = models.IntegerField()
    n3 = models.IntegerField()
    n4 = models.IntegerField()
    n5 = models.IntegerField()
    n6 = models.IntegerField()
    pick_type = models.CharField('구매방식', max_length=1, choices=PICK_CHOICES)
    price = models.IntegerField('금액', default=1000)
    purchased_at = models.DateTimeField('구매일시', default=timezone.now)
    rank = models.IntegerField('당첨순위', default=0)   # 0 = 미당첨, 1~5 = 등수
    prize = models.IntegerField('당첨금', default=0)

    class Meta:
        ordering = ['-purchased_at']

    def numbers(self):
        return sorted([self.n1, self.n2, self.n3, self.n4, self.n5, self.n6])

    @classmethod
    def auto_pick(cls):
        # 자동번호 생성: 1~45 중 6개 무작위 선택
        return sorted(random.sample(range(1, 46), 6))

    def check_winning(self):
        # 이 티켓의 당첨 여부 판정 후 rank, prize 갱신
        rnd = self.draw_round
        if not rnd.is_drawn:
            return
        win = set(rnd.winning_numbers())
        mine = set(self.numbers())
        match = len(win & mine)
        bonus_hit = rnd.bonus in mine

        if match == 6:
            self.rank, self.prize = 1, 2_000_000_000
        elif match == 5 and bonus_hit:
            self.rank, self.prize = 2, 50_000_000
        elif match == 5:
            self.rank, self.prize = 3, 1_500_000
        elif match == 4:
            self.rank, self.prize = 4, 50_000
        elif match == 3:
            self.rank, self.prize = 5, 5_000
        else:
            self.rank, self.prize = 0, 0
        self.save()