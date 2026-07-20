from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import F
from .models import FAQ, ChatSession, ChatMessage, UnansweredQuestion
from spellchecker import SpellChecker
from django.contrib.auth.decorators import login_required

spell = SpellChecker()

CUSTOM_WORDS = [
    "kpit",
    "msbte",
    "aiml",
    "cgpa",
    "semester",
    "hostel",
    "admission",
    "syllabus",
    "principal",
    "hod",
]

spell.word_frequency.load_words(CUSTOM_WORDS)


def auth_page(request):

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── LOGIN ──────────────────────────────
        if action == 'login':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'login_error:Invalid username or password')

        # ── SIGNUP ─────────────────────────────
        elif action == 'signup':
            username = request.POST.get('username')
            password = request.POST.get('password')
            confirm  = request.POST.get('confirm_password')

            if password != confirm:
                messages.error(request, 'signup_error:Passwords do not match')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'signup_error:Username already taken')
            elif len(password) < 6:
                messages.error(request, 'signup_error:Password must be at least 6 characters')
            else:
                User.objects.create_user(username=username, password=password)
                messages.success(request, 'signup_success:Account created! You can now log in.')

        # ── FORGOT PASSWORD ────────────────────
        elif action == 'forgot':
            username = request.POST.get('username')
            new_pass = request.POST.get('new_password')
            confirm  = request.POST.get('confirm_new_password')

            if not User.objects.filter(username=username).exists():
                messages.error(request, 'forgot_error:No account found with that username')
            elif new_pass != confirm:
                messages.error(request, 'forgot_error:Passwords do not match')
            elif len(new_pass) < 6:
                messages.error(request, 'forgot_error:Password must be at least 6 characters')
            else:
                user = User.objects.get(username=username)
                user.set_password(new_pass)
                user.save()
                messages.success(request, 'forgot_success:Password reset! You can now log in.')

    return render(request, 'auth.html')


def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('auth')
    return render(request, 'dashboard.html')


def chatbot_view(request):
    if not request.user.is_authenticated:
        return redirect('auth')

    sessions = ChatSession.objects.filter(
        user=request.user
    ).order_by("-updated_at")

    return render(request, "chatbot.html", {
        "sessions": sessions
    })


FALLBACK_ANSWER = (
    "I don't have information on that yet. Please contact the college office, "
    "or try rephrasing your question."
)

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "am", "be", "been",
    "what", "when", "where", "who", "how", "do", "does", "did",
    "tell", "me", "about", "my", "your", "i", "you", "please",
    "of", "for", "to", "in", "on", "at", "and", "or", "it", "this", "that",
}


def _tokenize(text):
    words = ''.join(ch if ch.isalnum() else ' ' for ch in text.lower()).split()
    return {w for w in words if w not in STOPWORDS}

def correct_sentence(sentence):
    words = sentence.split()
    corrected = []

    for word in words:
        # Keep numbers unchanged
        if word.isdigit():
            corrected.append(word)
            continue

        corrected_word = spell.correction(word.lower())

        corrected.append(corrected_word if corrected_word else word)

    return " ".join(corrected)

def find_best_faq_match(user_message, cutoff=0.5):
    """
    Compares the user's message against every FAQ question + keyword phrase
    using word-overlap similarity (ignoring common stopwords), and returns
    the best matching FAQ's answer. Returns None if nothing matches well enough.
    """
    user_message = user_message.strip()
    if not user_message:
        return None

    user_words = _tokenize(user_message)
    if not user_words:
        return None

    best_score = 0.0
    best_answer = None

    for faq in FAQ.objects.all():
        candidates = [faq.question]
        if faq.keywords:
            candidates += [k.strip() for k in faq.keywords.split(',') if k.strip()]

        for phrase in candidates:
            phrase_words = _tokenize(phrase)
            if not phrase_words:
                continue
            # Jaccard-style overlap, weighted toward how much of the *phrase* is covered
            overlap = user_words & phrase_words
            if not overlap:
                continue
            # How much of the *shorter* side is covered — handles short queries
            # like "ut date?" matching a longer keyword phrase well.
            score = len(overlap) / min(len(phrase_words), len(user_words))
            if score > best_score:
                best_score = score
                best_answer = faq.answer

    if best_score >= cutoff:
        return best_answer
    return None


def log_unanswered_question(user_message, user):
    """
    Records a question the FAQ system couldn't answer, so it shows up
    in the admin panel for review. If the same question (case-insensitive)
    was already logged and hasn't been resolved yet, just bump its counter
    instead of creating a duplicate row.
    """
    user_message = user_message.strip()
    if not user_message:
        return

    existing = UnansweredQuestion.objects.filter(
        question__iexact=user_message,
        is_resolved=False
    ).first()

    if existing:
        existing.times_asked = F('times_asked') + 1
        existing.save(update_fields=['times_asked', 'last_asked_at'])
    else:
        UnansweredQuestion.objects.create(
            question=user_message,
            asked_by=user if user.is_authenticated else None
        )


@csrf_exempt
def ask_ai(request):
    if request.method == "POST":
        data = json.loads(request.body)

        user_message = data.get("message", "")
        session_id = data.get("session_id")

        user_message = correct_sentence(user_message)

        # Create a new chat if none exists
        if session_id:
            session = ChatSession.objects.get(
                id=session_id,
                user=request.user
            )
        else:
            session = ChatSession.objects.create(
                user=request.user,
                title=user_message[:40]
            )

        # Save user's message
        ChatMessage.objects.create(
            session=session,
            sender="user",
            message=user_message
        )

        # Find answer
        matched_answer = find_best_faq_match(user_message)

        if matched_answer:
            answer = matched_answer
        else:
            answer = FALLBACK_ANSWER
            # No FAQ matched this question — log it so admins can review
            # it and add it to the FAQ table.
            log_unanswered_question(user_message, request.user)

        # Save bot's reply
        ChatMessage.objects.create(
            session=session,
            sender="bot",
            message=answer
        )

        return JsonResponse({
            "answer": answer,
            "session_id": session.id
        })

    return JsonResponse({"error": "POST request required"}, status=400)

@login_required
def load_chat(request, session_id):
    try:
        session = ChatSession.objects.get(
            id=session_id,
            user=request.user
        )

        messages = []

        for msg in session.messages.all().order_by("created_at"):
            messages.append({
                "sender": msg.sender,
                "message": msg.message
            })

        return JsonResponse({
            "success": True,
            "session_id": session.id,
            "messages": messages
        })

    except ChatSession.DoesNotExist:
        return JsonResponse({
            "success": False
        }, status=404)
    
def logout_view(request):
    logout(request)
    return redirect('auth')