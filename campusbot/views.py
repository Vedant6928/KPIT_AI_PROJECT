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
"""I couldn't find information related to your question.

Please try asking in a different way or contact the College Office for further assistance.

Here are some topics I can help with:

- Admissions
- Fees
- Scholarships
- Placements
- Library
- Bus Routes
- Departments
- Examinations
- Campus Facilities"""
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

GREETING_WORDS = {
    "hi", "hii", "hiii", "hello", "hey", "heya", "hola",
    "goodmorning", "goodafternoon", "goodevening",
}

GREETING_RESPONSE = (
"""### 👋 Hello!

I'm **ASKKPIT**, the AI assistant for **K. P. Patil Institute of Technology**.

I can help you with information about:

- Admissions
- Courses
- Fees
- Scholarships
- Placements
- Internships
- Library
- Bus Routes
- Departments
- Examinations
- Campus Facilities

Just ask your question in natural language, and I'll do my best to help."""
)

IDENTITY_PHRASES = {
    "who are you",
    "what are you",
    "who r u",
    "what is your name",
    "whats your name",
    "what's your name",
    "tell me about yourself",
    "your name",
}

IDENTITY_RESPONSE = (
"""### 🎓 About ASKKPIT

I am **ASKKPIT**, the official AI-powered college assistant for **K. P. Patil Institute of Technology**.

I can help you with information about:

- Admissions
- Courses
- Fees
- Scholarships
- Placements
- Internships
- Library
- Bus Routes
- Departments
- Examinations
- Campus Facilities

Simply ask your question in natural language, and I'll do my best to help."""
)

THANKS_WORDS = {
    "thanks", "thank", "thankyou", "thanku", "thnx", "thx", "ty",
}

THANKS_RESPONSE = (
    "You're welcome! 😊 Let me know if you have any other questions about KPIT."
)

BYE_WORDS = {
    "bye", "byebye", "goodbye", "gudbye", "seeya", "cya", "byee",
    "see", "ya",
}

BYE_RESPONSE = (
    "Goodbye! 👋 Feel free to come back anytime you have questions about KPIT."
)


def detect_smalltalk_response(user_message):
    """
    Checks the user's message for simple greetings (hi/hello/hey...),
    identity questions (who are you / what's your name...), thanks, or
    goodbyes, and returns an appropriate canned response. Returns None
    if it's none of these, so the caller can fall back to normal FAQ
    matching.
    """
    normalized = user_message.strip().lower()
    normalized = ''.join(ch for ch in normalized if ch.isalnum() or ch.isspace())
    normalized = ' '.join(normalized.split())  # collapse extra spaces

    if not normalized:
        return None

    # Identity questions first (checked as substrings so phrasing can vary
    # slightly, e.g. "hey who are you" still matches).
    for phrase in IDENTITY_PHRASES:
        if phrase in normalized:
            return IDENTITY_RESPONSE

    words = normalized.split()
    FILLER = {"there", "bot", "buddy", "friend", "so", "much", "you", "u", "very", "for", "help", "your", "help", "and", "again", "all", "the"}

    # Thanks: e.g. "thanks", "thank you", "thank you so much", "thanks a lot"
    if words and any(w in THANKS_WORDS for w in words) and \
            all(w in THANKS_WORDS or w in FILLER or w == "a" or w == "lot" for w in words):
        return THANKS_RESPONSE

    # Bye: e.g. "bye", "goodbye", "bye bye", "see you", "see ya"
    if words and any(w in BYE_WORDS for w in words) and \
            all(w in BYE_WORDS or w in FILLER for w in words):
        return BYE_RESPONSE

    # Greeting words: match if the whole message is just greeting word(s)
    # plus harmless filler like "there"/"bot", e.g. "hi", "hello there",
    # "hey hey" — but not when the greeting is only part of a longer real
    # question like "hi what is the fee structure".
    if words and any(w in GREETING_WORDS for w in words) and \
            all(w in GREETING_WORDS or w in FILLER for w in words):
        return GREETING_RESPONSE

    return None


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

        # Check for smalltalk first (greetings like "hi"/"hello",
        # identity questions like "who are you") before hitting the FAQs.
        smalltalk_answer = detect_smalltalk_response(user_message)

        if smalltalk_answer:
            answer = smalltalk_answer
        else:
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