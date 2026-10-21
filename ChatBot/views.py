import json

from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from ChatBot.llm_utility import app

questions = []
def homepage(request):
    return render(request, "ChatBot/index.html")


@require_POST
@csrf_protect
def chat(request):
    global questions
    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "Invalid request."},
            status=400
        )

    if not question:
        return JsonResponse(
            {"error": "Please enter a question."},
            status=400
        )

    questions.insert(0, question)

    # Keep only latest 5 questions
    questions = questions[:5]

    try:
        result = app.invoke({"question": question})

        return JsonResponse({
            "topic": result.get("topic", "general"),
            "answer": result.get("answer", ""),
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "recent_questions": questions
        })

    except Exception as error:

        return JsonResponse(
            {"error": "Unable to generate a response. Check the server terminal."},
            status=500
        )