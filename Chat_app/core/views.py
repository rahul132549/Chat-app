from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from .models import User, Message
from .forms import RegisterForm, LoginForm

# -------------------- REGISTER --------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect('user-list')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('user-list')

    return render(request, 'register.html', {'form': form})

# -------------------- LOGIN --------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('user-list')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        # IMPORTANT: username=email because USERNAME_FIELD='email'
        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)
            user.is_online = True
            user.save()
            return redirect('user-list')
        else:
            form.add_error(None, 'Invalid email or password')

    return render(request, 'login.html', {'form': form})

# -------------------- LOGOUT --------------------
@login_required
def logout_view(request):
    user = request.user
    user.is_online = False
    user.last_seen = timezone.now()
    user.save()
    logout(request)
    return redirect('login')

# -------------------- USER LIST --------------------
@login_required
def user_list(request):
    users = User.objects.exclude(id=request.user.id).annotate(
        unread_count=Count('sent_messages', filter=Q(sent_messages__is_read=False, sent_messages__receiver=request.user))
    )
    return render(request, 'user_list.html', {'users': users})

# -------------------- CHAT --------------------
@login_required
def chat_view(request, user_id):
    try:
        other_user = User.objects.get(id=user_id)

        # Mark messages as read
        Message.objects.filter(
            sender=other_user,
            receiver=request.user,
            is_read=False
        ).update(is_read=True)

        messages = Message.objects.filter(
            Q(sender=request.user, receiver=other_user) |
            Q(sender=other_user, receiver=request.user)
        ).order_by('timestamp')

        context = {
            'other_user': other_user,
            'messages': messages,
        }
        return render(request, 'chat.html', context)
    except User.DoesNotExist:
        return redirect('user-list')