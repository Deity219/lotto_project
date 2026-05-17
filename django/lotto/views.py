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


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('lotto:index')
    else:
        form = UserCreationForm()
    return render(request, 'lotto/signup.html', {'form': form})


# 일반 사용자 기능
@login_required
def buy(request):
    # 수동/자동 구매. 미추첨 상태의 최신 회차에 티켓 발급.
    current = DrawRound.objects.filter(is_drawn=False).order_by('round_no').first()
    if current is None:
        return render(request, 'lotto/buy.html',
                      {'error': '판매 중인 회차가 없습니다. 관리자에게 문의하세요.'})

    if request.method == 'POST':
        mode = request.POST.get('mode')
        if mode == 'manual':
            form = ManualTicketForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                Ticket.objects.create(
                    user=request.user, draw_round=current,
                    n1=cd['n1'], n2=cd['n2'], n3=cd['n3'],
                    n4=cd['n4'], n5=cd['n5'], n6=cd['n6'],
                    pick_type=Ticket.PICK_MANUAL,
                )
                return redirect('lotto:my_tickets')
        else:  # auto
            form = AutoTicketForm(request.POST)
            if form.is_valid():
                for _ in range(form.cleaned_data['count']):
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
        'manual_form': ManualTicketForm(),
        'auto_form': AutoTicketForm(),
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