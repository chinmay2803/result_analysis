from django.db import models

class StudentResult(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    total_marks = models.IntegerField()
    percentage = models.FloatField()
    grade = models.CharField(max_length=5)
    subject1 = models.FloatField()
    subject2 = models.FloatField()
    subject3 = models.FloatField()
    subject4 = models.FloatField()

    def __str__(self):
        return self.name
