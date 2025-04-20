import json
import logging
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from .models import *
import random

OPENROUTER_API_KEY = "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"  # replace this
OPENROUTER_MODEL = "openai/gpt-3.5-turbo"  # or mistralai/mistral-7b-instruct, etc.
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer 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",
    "Content-Type": "application/json"
}

def start_page(request):
    return render(request, 'start_page.html')

def results_page(request):
    score = int(request.GET.get('score', 0))
    total = int(request.GET.get('total', 0))

    # Debug to check values
    print(f"Score: {score}, Total: {total}")

    context = {
        'score': score,
        'total': total,
    }
    return render(request, 'results.html', context)

def home(request):
    # Reset session to allow reattempt
    request.session['quiz_completed'] = False
    context = {'categories': Category.objects.all()}
    if request.GET.get('category'):
        return redirect(f"/quiz/?category={request.GET.get('category')}")
    return render(request, 'home.html', context)

def quiz(request):
    if request.session.get('quiz_completed', False):
        return redirect('home')
    category = request.GET.get('category', '')
    context = {'category': category}
    return render(request, 'quiz.html', context)

def get_quiz(request):
    try:
        if request.session.get('quiz_completed', False):
            return redirect('home')

        question_objs = Question.objects.all()

        if request.GET.get('category'):
            question_objs = Question.objects.filter(category__category_name__icontains=request.GET.get('category'))

        question_objs = list(question_objs)

        data = []
        random.shuffle(question_objs)

        # Limit to 10 random questions
        question_objs = question_objs[:10]

        for question_obj in question_objs:
            data.append({
                "uid": question_obj.uid,
                "category": question_obj.category.category_name,
                "question": question_obj.question,
                "marks": 1,  # Set default marks to 1
                "answers": question_obj.get_answer()
            })

        payload = {'status': True, 'data': data}
        return JsonResponse(payload)

    except Exception as e:
        print(e)
    return HttpResponse("Something Went Wrong")


import re  # make sure this is at the top

@csrf_exempt
def ai_quiz_view(request):
    import re

    def parse_quiz_response(text):
        quiz = []
        raw_questions = re.split(r'Question \d+:', text)[1:]  # updated regex
        print(f"🔍 Total questions found: {len(raw_questions)}")

        for i, q_block in enumerate(raw_questions):
            lines = q_block.strip().split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            print(f"➡️ Q{i + 1} lines: {lines}")

            # Check if we have at least 6 lines: 1 question + 4 options + 1 answer
            if len(lines) < 6:
                print(f"⚠️ Skipping incomplete question block: {lines}")
                continue

            question_text = lines[0]
            options = lines[1:5]

            answer_line = next((line for line in lines if line.lower().startswith('answer:')), None)
            if answer_line:
                answer = answer_line.split(":", 1)[-1].strip()
                if '.' in answer:
                    answer = answer.split('.', 1)[-1].strip()
            else:
                answer = "N/A"

            quiz.append({
                'question': question_text,
                'options': options,
                'answer': answer
            })

            print(f"✅ Parsed Q{i + 1}: {question_text}, Answer: {answer}")

        return quiz

    if request.method == 'POST':
        topic = request.POST.get('topic')
        print(f"🧠 Topic received: {topic}")

        full_prompt = (
            f"Generate 5 beginner-level multiple choice questions on the topic '{topic}'. "
            "Each question should have 4 options labeled A, B, C, and D. "
            "Randomize the correct answer — it can be any one of A, B, C, or D. "
            "At the end of each question, provide the correct answer like this: "
            "Answer: [correct option letter]. [option text]"
        )

        try:
            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful quiz generator."},
                        {"role": "user", "content": full_prompt}
                    ]
                }
            )

            if response.status_code == 200:
                raw_text = response.json()['choices'][0]['message']['content']

                # Remove the echoed prompt if present
                if full_prompt in raw_text:
                    raw_text = raw_text.split(full_prompt)[-1]

                print("📝 Raw AI Output:\n", raw_text[:1000])  # Print first 1000 chars

                questions = parse_quiz_response(raw_text)

                if not questions:
                    return render(request, 'ai_quiz_display.html', {'error': 'No questions parsed. Please try again.'})

                request.session['ai_quiz_data'] = questions
                return render(request, 'ai_quiz_display.html', {
                    'quiz': questions,
                    'show_answers': False
                })


            print(f"❌ API failed with status {response.status_code}: {response.text}")
            return render(request, 'ai_quiz_display.html', {'error': 'Failed to fetch data from AI API.'})

        except Exception as e:
            print(f"🚨 Exception occurred: {e}")
            return render(request, 'ai_quiz_display.html', {'error': 'An unexpected error occurred.'})

    return render(request, 'ai_quiz_input.html')


import re

def clean(text):
    return re.sub(r'^[A-Da-d][\.\)]\s*', '', text.strip().lower()).strip('. ')

def submit_ai_quiz(request):
    quiz_data = request.session.get('ai_quiz_data', [])
    score = 0
    total = len(quiz_data)

    # Get user's answers from POST
    user_answers = {}
    for key, value in request.POST.items():
        if key.startswith('q'):  # Question keys are like q1, q2, etc.
            user_answers[key] = value.strip()

    print("User Answers:", user_answers)

    # Attach user's selected answers and normalize for comparison
    for idx, question in enumerate(quiz_data):
        q_key = f"q{idx+1}"
        selected = user_answers.get(q_key, "")
        question['selected'] = selected

        # Just to be safe, set the answer explicitly again
        correct_answer = question.get('answer', '').strip()
        question['answer'] = correct_answer


        # Compare normalized values
        cleaned_selected = clean(selected)
        cleaned_answer = clean(correct_answer)

        question['selected_clean'] = cleaned_selected
        question['answer_clean'] = cleaned_answer

        if cleaned_selected == cleaned_answer:
            score += 1

    return render(request, 'ai_quiz_display.html', {
        'quiz': quiz_data,
        'show_answers': True,
        'score': score,
        'total': total
    })

def submit_quiz(request):
    if request.method == 'POST':
        try:
            # Parse JSON payload
            body = json.loads(request.body)
            score = body.get('score', 0)
            total = body.get('total', 0)

            # Save results or perform logic here if needed
            print(f"Score: {score}, Total: {total}")

            # Return a success response
            return JsonResponse({'message': 'Quiz submitted successfully'}, status=200)
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

def reset_quiz(request):
    request.session['quiz_completed'] = False
    return redirect('home')

def home_view(request):
    request.session.pop('quiz_completed', None)  # Clear session on home
    return render(request, 'home.html')

# New Views for Login and Signup
def login_view(request):
    return render(request, 'login.html')  # You need to create a login.html template

def signup_view(request):
    return render(request, 'signup.html')  # You need to create a signup.html template