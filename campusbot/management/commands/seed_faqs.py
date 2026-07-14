from django.core.management.base import BaseCommand
from campusbot.models import FAQ


STARTER_FAQS = [
    {
        "question": "What are the admission requirements?",
        "answer": "Admissions require your 12th grade marksheet, a valid ID, and entrance exam score where applicable. Applications open every June.",
        "category": "admission",
        "keywords": "admission process, how to apply, eligibility criteria, admission criteria",
    },
    {
        "question": "What is the fee structure?",
        "answer": "Tuition ranges from ₹50,000 to ₹1,20,000 per year depending on the program. Scholarships are available for merit and need-based cases.",
        "category": "fees",
        "keywords": "tuition fees, semester fee, course fee, how much is the fee",
    },
    {
        "question": "What courses are offered?",
        "answer": "We offer Computer Science, Mechanical Engineering, Civil Engineering, Business Administration, and Design programs.",
        "category": "academic",
        "keywords": "branches available, programs offered, departments, what can i study",
    },
    {
        "question": "When is the unit test?",
        "answer": "UT1 is scheduled from 10th to 14th August 2026. Please check the notice board for subject-wise timings.",
        "category": "academic",
        "keywords": "unit test date, ut1 schedule, next unit test, exam schedule",
    },
    {
        "question": "Is hostel facility available?",
        "answer": "No hostel facility is available at the college.",
        "category": "hostel",
        "keywords": "hostel, hostel facility, hostel timings, hostel rules, hostel availability, is hostel available, tell me about hostel, hostel accommodation",
    },
]


class Command(BaseCommand):
    help = "Seeds the database with starter FAQ entries for AskKPIT"

    def handle(self, *args, **options):
        created_count = 0
        for item in STARTER_FAQS:
            _, created = FAQ.objects.get_or_create(
                question=item["question"],
                defaults={
                    "answer": item["answer"],
                    "category": item["category"],
                    "keywords": item["keywords"],
                },
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created_count} new FAQ entries ({len(STARTER_FAQS)} total defined)."
        ))
