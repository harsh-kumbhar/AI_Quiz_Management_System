import uuid
from django.db import models
import random

class BaseModel(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    class Meta:
        abstract = True

class Category(BaseModel):
    category_name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.category_name

class Question(BaseModel):
    category = models.ForeignKey(Category, related_name='category', on_delete=models.CASCADE)
    question = models.CharField(max_length=100, unique=True)
    marks = models.IntegerField(default=1)

    def __str__(self) -> str:
        return self.question

    def get_answer(self):
        answer_objs = list(Answer.objects.filter(question = self))
        data = []
        random.shuffle(answer_objs)
        for answer_obj in answer_objs:
            data.append({
                'answer' : answer_obj.answer,
                'is_correct' : answer_obj.is_correct
            })

        return data

class Answer(BaseModel):
    question = models.ForeignKey(Question, related_name='question_answer', on_delete=models.CASCADE)
    answer = models.CharField(max_length=100)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('question', 'answer')

    def __str__(self) -> str:
        return f"{self.answer} (Correct: {self.is_correct})"
