from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Sum
from .models import DrawRound, Ticket
from .forms import ManualTicketForm, AutoTicketForm


def index(request):
    latest = DrawRound.objects.filter(is_drawn=True).first()
    return render(request, 'lotto/index.html', {'latest': latest})


from .forms import ManualTicketForm, AutoTicketForm, KoreanUserCreationForm

def signup(request):
    if request.method == 'POST':
        form = KoreanUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('lotto:index')
    else:
        form = KoreanUserCreationForm()
    return render(request, 'lotto/signup.html', {'form': form})


# 일반 사용자 기능
@login_required
def buy(request):
    current = DrawRound.objects.filter(is_drawn=False).order_by('round_no').first()
    if current is None:
        return render(request, 'lotto/buy.html',
                      {'error': '판매 중인 회차가 없습니다. 관리자에게 문의하세요.'})

    error = None  # 에러 메시지

    if request.method == 'POST':
        mode = request.POST.get('mode')

        if mode == 'manual':
            try:
                nums = [int(request.POST.get(f'n{i}')) for i in range(1, 7)]
            except (TypeError, ValueError):
                error = '번호는 정수만 입력 가능합니다.'
            else:
                if any(n < 1 or n > 45 for n in nums):
                    error = '번호는 1~45 사이여야 합니다.'
                elif len(set(nums)) != 6:
                    error = '6개 번호는 모두 달라야 합니다. 중복된 번호가 있습니다.'
                else:
                    # 매수 제한 체크
                    MAX_PER_USER = 5
                    already_have = Ticket.objects.filter(
                        user=request.user, draw_round=current
                    ).count()
                    if already_have >= MAX_PER_USER:
                        error = f'이번 회차에는 이미 최대({MAX_PER_USER}매)까지 구매하셨습니다.'
                    else:
                        Ticket.objects.create(
                            user=request.user, draw_round=current,
                            n1=nums[0], n2=nums[1], n3=nums[2],
                            n4=nums[3], n5=nums[4], n6=nums[5],
                            pick_type=Ticket.PICK_MANUAL,
                        )
                        return redirect('lotto:my_tickets')

        elif mode == 'auto':
            try:
                count = int(request.POST.get('count', 1))
            except ValueError:
                count = 1
            count = max(1, min(5, count))  # 1회 요청당 1~5매 제한

            # 한 회차당 한 사람이 보유 가능한 최대 매수 (예: 5매)
            MAX_PER_USER = 5
            already_have = Ticket.objects.filter(user=request.user, draw_round=current).count()

        if already_have + count > MAX_PER_USER:
            remaining = MAX_PER_USER - already_have
            if remaining <= 0:
                error = f'이번 회차에는 이미 최대({MAX_PER_USER}매)까지 구매하셨습니다.'
            else:
                error = f'이번 회차에는 최대 {MAX_PER_USER}매까지 구매 가능합니다. (현재 {already_have}매 보유, {remaining}매 더 구매 가능)'
        else:
            for _ in range(count):
                nums = Ticket.auto_pick()
                Ticket.objects.create(
                    user=request.user, draw_round=current,
                    n1=nums[0], n2=nums[1], n3=nums[2],
                    n4=nums[3], n5=nums[4], n6=nums[5],
                    pick_type=Ticket.PICK_AUTO,
                )
            return redirect('lotto:my_tickets')

    return render(request, 'lotto/buy.html', {
        'current': current,
        'error': error,
        'already_have': Ticket.objects.filter(
            user=request.user, draw_round=current
        ).count(),
        'max_per_user': 5,
    })


@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, 'lotto/my_tickets.html', {'tickets': tickets})


@login_required
def check(request):
    # 당첨 확인: 본인이 산 티켓 중 추첨 완료된 회차 결과
    tickets = Ticket.objects.filter(
        user=request.user, draw_round__is_drawn=True
    ).select_related('draw_round')
    return render(request, 'lotto/check.html', {'tickets': tickets})


# 관리자 기능
def is_staff(u):
    return u.is_authenticated and u.is_staff


@user_passes_test(is_staff)
def admin_dashboard(request):
    rounds = DrawRound.objects.all()
    return render(request, 'lotto/admin_dashboard.html', {'rounds': rounds})


@user_passes_test(is_staff)
def admin_sales(request):
    # 판매 내역: 회차별 매출 / 매수 집계
    rows = (Ticket.objects.values('draw_round__round_no')
            .annotate(cnt=Count('id'), revenue=Sum('price'))
            .order_by('-draw_round__round_no'))
    return render(request, 'lotto/sales.html', {'rows': rows})


@user_passes_test(is_staff)
def admin_draw(request):
    # 추첨 기능: 미추첨 회차를 골라 무작위 6+보너스 추첨
    if request.method == 'POST':
        round_id = request.POST.get('round_id')
        rnd = get_object_or_404(DrawRound, id=round_id, is_drawn=False)
        rnd.execute_draw()
        # 모든 티켓에 대해 당첨 판정
        for t in rnd.tickets.all():
            t.check_winning()
        # 다음 회차 자동 생성
        next_no = rnd.round_no + 1
        DrawRound.objects.get_or_create(round_no=next_no)
        return redirect('lotto:admin_draw')
    pending = DrawRound.objects.filter(is_drawn=False)
    done = DrawRound.objects.filter(is_drawn=True)[:5]
    return render(request, 'lotto/draw.html', {'pending': pending, 'done': done})


@user_passes_test(is_staff)
def admin_winners(request):
    # 당첨 내역
    winners = Ticket.objects.filter(rank__gt=0).select_related('user', 'draw_round')
    return render(request, 'lotto/winners.html', {'winners': winners})