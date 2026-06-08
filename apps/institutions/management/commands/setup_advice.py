"""
apps/institutions/management/commands/setup_advice.py
Seeds the database with demo institutions, users, sessions, wellness checks, and goals.
Run: python manage.py setup_advice
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
import random


class Command(BaseCommand):
    help = 'Set up ADVICE platform with demo data'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete all existing data first')

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting database...')
            self._reset()

        self.stdout.write(self.style.WARNING('Setting up ADVICE demo data...'))

        institution = self._create_institution()
        admin = self._create_admin(institution)
        counselors = self._create_counselors(institution)
        students = self._create_students(institution)
        self._create_sessions(students, counselors)
        self._create_wellness_checks(students)
        self._create_goals(students, counselors)
        self._create_notifications(students, counselors)
        self._create_conversations(students, counselors)
        self._create_subscription(institution)

        self.stdout.write(self.style.SUCCESS('\n✅ ADVICE demo setup complete!\n'))
        self.stdout.write('━' * 50)
        self.stdout.write(self.style.SUCCESS('Login credentials:'))
        self.stdout.write(f'  Student:   student@demo.edu  / Demo1234!')
        self.stdout.write(f'  Counselor: counselor@demo.edu / Demo1234!')
        self.stdout.write(f'  Admin:     admin@demo.edu     / Demo1234!')
        self.stdout.write(f'  Super Admin: super@advice.com / Demo1234!')
        self.stdout.write('━' * 50)
        self.stdout.write(f'  URL: http://127.0.0.1:8000/')
        self.stdout.write('')

    def _reset(self):
        from apps.accounts.models import User, InvitationCode
        from apps.institutions.models import Institution
        from apps.counseling.models import CounselingSession, GroupSession, SessionFeedback
        from apps.messaging.models import Conversation, Message, Notification
        from apps.progress.models import WellnessCheck, ProgressGoal, CrisisAlert
        from apps.payments.models import SubscriptionPlan, InstitutionSubscription, PaymentRecord

        for model in [PaymentRecord, InstitutionSubscription, CrisisAlert, ProgressGoal,
                      WellnessCheck, Message, Notification, Conversation, SessionFeedback,
                      CounselingSession, GroupSession, InvitationCode, User, Institution]:
            count = model.objects.count()
            model.objects.all().delete()
            self.stdout.write(f'  Deleted {count} {model.__name__} records')

    def _create_institution(self):
        from apps.institutions.models import Institution
        inst, created = Institution.objects.get_or_create(
            slug='demo',
            defaults={
                'name': 'Demo University',
                'description': 'A leading university committed to student wellbeing.',
                'email': 'admin@demo.edu',
                'phone': '+254 700 000 000',
                'website': 'https://demo.edu',
                'address': 'University Avenue, Nairobi, Kenya',
                'country': 'Kenya',
                'plan': 'professional',
                'status': 'active',
                'plan_expires_at': timezone.now() + timedelta(days=365),
                'allow_student_self_registration': True,
                'require_invitation_code': False,
                'enable_peer_support': True,
                'enable_group_sessions': True,
            }
        )
        verb = 'Created' if created else 'Found existing'
        self.stdout.write(f'  {verb} institution: {inst.name}')
        return inst

    def _create_admin(self, institution):
        from apps.accounts.models import User

        # Super admin
        super_admin, _ = User.objects.get_or_create(
            email='super@advice.com',
            defaults={
                'first_name': 'Platform',
                'last_name': 'Admin',
                'role': User.SUPER_ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'email_verified': True,
                'is_active': True,
            }
        )
        super_admin.set_password('Demo1234!')
        super_admin.save()

        # Institution admin
        admin, _ = User.objects.get_or_create(
            email='admin@demo.edu',
            defaults={
                'first_name': 'Grace',
                'last_name': 'Wanjiku',
                'role': User.INSTITUTION_ADMIN,
                'institution': institution,
                'email_verified': True,
                'is_active': True,
            }
        )
        admin.set_password('Demo1234!')
        admin.institution = institution
        admin.save()

        self.stdout.write(f'  Created admin users')
        return admin

    def _create_counselors(self, institution):
        from apps.accounts.models import User
        from apps.counseling.models import CounselorAvailability

        counselor_data = [
            {
                'email': 'counselor@demo.edu',
                'first_name': 'Dr. Sarah',
                'last_name': 'Johnson',
                'bio': 'Specialist in cognitive behavioural therapy with 8 years of experience helping students overcome anxiety, depression, and academic stress.',
                'license_number': 'KPS-2016-4821',
                'specializations': ['Anxiety', 'Depression', 'CBT', 'Academic Stress'],
                'years_experience': 8,
            },
            {
                'email': 'counselor2@demo.edu',
                'first_name': 'Dr. James',
                'last_name': 'Omondi',
                'bio': 'Trauma-informed counselor focusing on grief, relationship challenges, and identity development in young adults.',
                'license_number': 'KPS-2018-7743',
                'specializations': ['Trauma', 'Grief', 'Relationships', 'Identity'],
                'years_experience': 6,
            },
            {
                'email': 'counselor3@demo.edu',
                'first_name': 'Ms. Amina',
                'last_name': 'Hassan',
                'bio': 'Certified school counselor with expertise in career guidance, social skills, and stress management.',
                'license_number': 'KPS-2020-3356',
                'specializations': ['Career', 'Social Skills', 'Stress Management'],
                'years_experience': 4,
            },
        ]

        counselors = []
        for data in counselor_data:
            c, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': User.COUNSELOR,
                    'institution': institution,
                    'email_verified': True,
                    'is_active': True,
                    'is_verified': True,
                    'bio': data['bio'],
                    'license_number': data['license_number'],
                    'specializations': data['specializations'],
                    'years_experience': data['years_experience'],
                    'max_students': 30,
                }
            )
            c.set_password('Demo1234!')
            c.institution = institution
            c.save()
            counselors.append(c)

            # Add availability
            for day in [0, 1, 2, 3, 4]:  # Mon–Fri
                CounselorAvailability.objects.get_or_create(
                    counselor=c,
                    day_of_week=day,
                    start_time='09:00',
                    defaults={'end_time': '17:00', 'is_active': True}
                )

        self.stdout.write(f'  Created {len(counselors)} counselors')
        return counselors

    def _create_students(self, institution):
        from apps.accounts.models import User

        student_data = [
            {'email': 'student@demo.edu', 'first_name': 'Alex', 'last_name': 'Mwangi', 'course': 'BSc Computer Science', 'year': 3, 'gender': 'M'},
            {'email': 'student2@demo.edu', 'first_name': 'Fatuma', 'last_name': 'Abubakar', 'course': 'BA Psychology', 'year': 2, 'gender': 'F'},
            {'email': 'student3@demo.edu', 'first_name': 'Brian', 'last_name': 'Kariuki', 'course': 'BEng Mechanical', 'year': 4, 'gender': 'M'},
            {'email': 'student4@demo.edu', 'first_name': 'Amelia', 'last_name': 'Owino', 'course': 'BSc Nursing', 'year': 1, 'gender': 'F'},
            {'email': 'student5@demo.edu', 'first_name': 'David', 'last_name': 'Njoroge', 'course': 'BCom Accounting', 'year': 2, 'gender': 'M'},
        ]

        students = []
        for data in student_data:
            s, _ = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': User.STUDENT,
                    'institution': institution,
                    'email_verified': True,
                    'is_active': True,
                    'course': data['course'],
                    'year_of_study': data['year'],
                    'gender': data['gender'],
                    'student_id': f'STU{random.randint(1000,9999)}',
                }
            )
            s.set_password('Demo1234!')
            s.institution = institution
            s.save()
            students.append(s)

        self.stdout.write(f'  Created {len(students)} students')
        return students

    def _create_sessions(self, students, counselors):
        from apps.counseling.models import CounselingSession, GroupSession, GroupSessionParticipant, SessionFeedback

        now = timezone.now()
        sessions_created = 0

        session_configs = [
            # (student_idx, counselor_idx, days_from_now, status, reason)
            (0, 0, 2, 'scheduled', 'Struggling with exam anxiety and difficulty concentrating during study sessions.'),
            (0, 0, -7, 'completed', 'Feeling overwhelmed with coursework and part-time job responsibilities.'),
            (1, 1, 1, 'scheduled', 'Experiencing grief after losing a close family member. Need support processing this.'),
            (1, 0, -14, 'completed', 'Ongoing anxiety about social situations and group work in university.'),
            (2, 2, 5, 'scheduled', 'Career guidance needed — unsure about future after graduation.'),
            (2, 0, -3, 'cancelled', 'Relationship difficulties causing depression and inability to focus.'),
            (3, 0, 3, 'scheduled', 'First-year transition struggles — feeling isolated and homesick.'),
            (4, 1, -5, 'completed', 'Managing stress related to financial pressures and academic performance.'),
            (0, 0, -1, 'in_progress', 'Follow-up session on coping strategies discussed last week.'),
        ]

        for s_idx, c_idx, days, status, reason in session_configs:
            student = students[s_idx % len(students)]
            counselor = counselors[c_idx % len(counselors)]
            scheduled_at = now + timedelta(days=days, hours=random.randint(9, 16))

            session, created = CounselingSession.objects.get_or_create(
                student=student,
                counselor=counselor,
                scheduled_at=scheduled_at,
                defaults={
                    'reason': reason,
                    'status': status,
                    'session_type': 'individual',
                    'mode': random.choice(['online', 'in_person']),
                    'duration_minutes': 60,
                    'student_mood_before': random.randint(3, 7),
                }
            )

            if status == 'completed' and created:
                session.summary = 'Session went well. Student showed good engagement with coping strategies.'
                session.counselor_notes = 'Private: Student making progress. Continue CBT exercises.'
                session.student_mood_after = random.randint(5, 9)
                session.ended_at = scheduled_at + timedelta(hours=1)
                session.follow_up_required = random.choice([True, False])
                session.save()

                # Add feedback for some
                if random.random() > 0.4:
                    SessionFeedback.objects.get_or_create(
                        session=session,
                        defaults={
                            'rating': random.randint(4, 5),
                            'was_helpful': True,
                            'comments': random.choice([
                                'Very helpful session. Dr. Johnson really listened.',
                                'I feel much better after talking things through.',
                                'Great advice on managing my time better.',
                                'The breathing exercises really help with anxiety.',
                            ]),
                            'would_recommend': True,
                        }
                    )
            sessions_created += 1

        # Group sessions
        for counselor in counselors[:2]:
            gs, _ = GroupSession.objects.get_or_create(
                title=random.choice([
                    'Stress Management Workshop',
                    'Mindfulness & Meditation Circle',
                    'Academic Success Strategies',
                    'Building Resilience Group',
                ]),
                facilitator=counselor,
                defaults={
                    'description': 'A supportive group session to share experiences and learn coping strategies together.',
                    'max_participants': 12,
                    'scheduled_at': now + timedelta(days=random.randint(3, 14), hours=14),
                    'duration_minutes': 90,
                    'topic': 'Mental Wellness',
                    'is_open': True,
                }
            )
            # Register some students
            for student in students[:3]:
                GroupSessionParticipant.objects.get_or_create(group_session=gs, user=student)

        self.stdout.write(f'  Created {sessions_created} counseling sessions + group sessions')

    def _create_wellness_checks(self, students):
        from apps.progress.models import WellnessCheck, CrisisAlert

        checks_created = 0
        today = timezone.now().date()

        patterns = {
            students[0]: {'mood': [6,7,5,8,7,6,8], 'anxiety': [5,4,6,3,5,4,3], 'sleep': [7,6,8,7,6,8,7]},
            students[1]: {'mood': [4,3,5,4,6,5,4], 'anxiety': [7,8,6,7,6,8,7], 'sleep': [5,4,6,5,7,5,6]},
            students[2]: {'mood': [7,8,7,9,8,7,8], 'anxiety': [3,2,4,2,3,2,3], 'sleep': [8,9,7,8,9,8,9]},
            students[3]: {'mood': [3,2,4,3,2,3,4], 'anxiety': [8,9,7,8,9,8,7], 'sleep': [4,3,5,4,3,5,4]},
        }

        for student, scores in patterns.items():
            days_count = len(scores['mood'])
            for i in range(days_count):
                check_date = today - timedelta(days=days_count - 1 - i)
                if WellnessCheck.objects.filter(student=student, date=check_date).exists():
                    continue
                try:
                    check = WellnessCheck.objects.create(
                        student=student,
                        mood_score=scores['mood'][i],
                        anxiety_level=scores['anxiety'][i],
                        sleep_quality=scores['sleep'][i],
                        energy_level=max(1, scores['mood'][i] - 1),
                        stress_level=11 - scores['mood'][i],
                        social_connection=scores['mood'][i],
                        notes='' if i < days_count - 1 else 'Feeling a bit stressed about upcoming exams.',
                        triggers=['exams', 'coursework'] if scores['mood'][i] < 5 else [],
                    )
                    check.date = check_date
                    check.save(update_fields=['date'])
                    checks_created += 1

                    # Crisis alert for very low scores
                    if check.flagged_for_review and student == students[3]:
                        from apps.counseling.models import CounselingSession
                        counselor_id = CounselingSession.objects.filter(
                            student=student
                        ).values_list('counselor', flat=True).first()
                        if counselor_id:
                            from apps.accounts.models import User
                            counselor = User.objects.get(id=counselor_id)
                            CrisisAlert.objects.get_or_create(
                                student=student,
                                counselor=counselor,
                                wellness_check=check,
                                defaults={
                                    'severity': 'high',
                                    'trigger_reason': f'Low mood ({check.mood_score}/10) and high anxiety ({check.anxiety_level}/10) detected.',
                                    'is_resolved': i < days_count - 2,
                                }
                            )
                except Exception:
                    pass  # skip duplicate dates

        self.stdout.write(f'  Created {checks_created} wellness checks')

    def _create_goals(self, students, counselors):
        from apps.progress.models import ProgressGoal

        goals_data = [
            (students[0], counselors[0], 'Manage exam anxiety', 'anxiety', 'Develop effective coping strategies to manage anxiety before and during examinations.', 65),
            (students[0], counselors[0], 'Improve sleep routine', 'lifestyle', 'Establish a consistent sleep schedule of 7-8 hours per night.', 40),
            (students[1], counselors[1], 'Process grief healthily', 'trauma', 'Work through grief in a healthy way and build a support network.', 30),
            (students[1], counselors[0], 'Build social confidence', 'social', 'Participate in at least one social activity per week on campus.', 70),
            (students[2], counselors[2], 'Clarify career path', 'career', 'Research career options and attend at least 3 career fairs this semester.', 80),
            (students[3], counselors[0], 'Reduce anxiety levels', 'anxiety', 'Practice mindfulness and breathing exercises daily to reduce anxiety scores.', 20),
            (students[4], counselors[1], 'Manage financial stress', 'stress', 'Create a budget and explore bursary opportunities to reduce financial pressure.', 55),
        ]

        for student, counselor, title, category, desc, progress in goals_data:
            goal, created = ProgressGoal.objects.get_or_create(
                student=student,
                title=title,
                defaults={
                    'counselor': counselor,
                    'description': desc,
                    'category': category,
                    'progress_percentage': progress,
                    'status': 'completed' if progress == 100 else 'active',
                    'target_date': (timezone.now() + timedelta(days=random.randint(30, 90))).date(),
                    'counselor_notes': 'Student is making good progress. Continue with current approach.',
                    'milestones': [
                        {'title': 'Initial assessment', 'completed': True},
                        {'title': 'First strategy session', 'completed': progress > 30},
                        {'title': 'Mid-point review', 'completed': progress > 60},
                        {'title': 'Goal achieved', 'completed': progress == 100},
                    ],
                }
            )

        self.stdout.write(f'  Created {len(goals_data)} goals')

    def _create_notifications(self, students, counselors):
        from apps.messaging.models import Notification

        notif_data = [
            (students[0], 'session_reminder', '📅 Session Reminder', 'Your session with Dr. Sarah Johnson is tomorrow at 10:00 AM.', '/sessions/'),
            (students[0], 'new_message', '💬 New Message', 'Dr. Johnson sent you a message.', '/messages/'),
            (students[0], 'progress_update', '📈 Goal Update', 'Your "Manage exam anxiety" goal has been updated.', '/goals/'),
            (students[1], 'session_reminder', '📅 Upcoming Session', 'Your session with Dr. James Omondi is in 2 days.', '/sessions/'),
            (students[1], 'invitation', '✉️ Welcome to ADVICE', 'Your account has been set up at Demo University.', '/'),
            (counselors[0], 'crisis_alert', '🚨 Student Needs Attention', 'Amelia Owino has submitted a low wellness check-in.', '/progress/crisis/'),
            (counselors[0], 'new_message', '💬 New Message', 'Alex Mwangi sent you a message.', '/messages/'),
        ]

        for recipient, ntype, title, body, url in notif_data:
            Notification.objects.get_or_create(
                recipient=recipient,
                title=title,
                defaults={
                    'notification_type': ntype,
                    'body': body,
                    'action_url': url,
                    'is_read': random.choice([True, False]),
                }
            )

        self.stdout.write(f'  Created demo notifications')

    def _create_conversations(self, students, counselors):
        from apps.messaging.models import Conversation, ConversationParticipant, Message

        pairs = [(students[0], counselors[0]), (students[1], counselors[1]), (students[3], counselors[0])]
        for student, counselor in pairs:
            conv, created = Conversation.objects.get_or_create(
                conversation_type='direct',
                title='',
                linked_session=None,
            )
            if created:
                ConversationParticipant.objects.get_or_create(conversation=conv, user=student)
                ConversationParticipant.objects.get_or_create(conversation=conv, user=counselor)

                messages_data = [
                    (counselor, f'Hi {student.first_name}, how are you doing today?'),
                    (student, 'I\'ve been feeling a bit anxious about my upcoming exams.'),
                    (counselor, 'That\'s completely understandable. Let\'s work through some strategies together in our next session. Have you tried the breathing exercises we discussed?'),
                    (student, 'Yes, they really help! Thank you so much.'),
                ]
                for sender, content in messages_data:
                    Message.objects.create(conversation=conv, sender=sender, content=content)

        self.stdout.write(f'  Created demo conversations')

    def _create_subscription(self, institution):
        from apps.payments.models import SubscriptionPlan, InstitutionSubscription, PaymentRecord

        plan, _ = SubscriptionPlan.objects.get_or_create(
            slug='professional',
            defaults={
                'name': 'Professional',
                'description': 'For growing institutions with up to 2,000 students.',
                'billing_cycle': 'annual',
                'price_usd': 5000,
                'max_students': 2000,
                'max_counselors': 20,
                'has_real_time_chat': True,
                'has_group_sessions': True,
                'has_analytics': True,
                'has_peer_support': True,
                'has_priority_support': True,
                'is_active': True,
                'sort_order': 2,
            }
        )

        # Starter plan
        SubscriptionPlan.objects.get_or_create(
            slug='starter',
            defaults={
                'name': 'Starter', 'description': 'For small institutions up to 500 students.',
                'billing_cycle': 'annual', 'price_usd': 2500,
                'max_students': 500, 'max_counselors': 5,
                'has_real_time_chat': True, 'has_group_sessions': True,
                'has_analytics': True, 'is_active': True, 'sort_order': 1,
            }
        )

        # Enterprise plan
        SubscriptionPlan.objects.get_or_create(
            slug='enterprise',
            defaults={
                'name': 'Enterprise', 'description': 'Unlimited students and counselors with custom pricing.',
                'billing_cycle': 'annual', 'price_usd': None,
                'has_real_time_chat': True, 'has_group_sessions': True,
                'has_analytics': True, 'has_custom_branding': True,
                'has_api_access': True, 'has_priority_support': True,
                'is_active': True, 'sort_order': 3,
            }
        )

        sub, _ = InstitutionSubscription.objects.get_or_create(
            institution=institution,
            defaults={
                'plan': plan,
                'status': 'active',
                'started_at': timezone.now() - timedelta(days=30),
                'current_period_start': timezone.now() - timedelta(days=30),
                'current_period_end': timezone.now() + timedelta(days=335),
                'student_count': 5,
            }
        )

        PaymentRecord.objects.get_or_create(
            institution=institution,
            gateway='stripe',
            defaults={
                'subscription': sub,
                'gateway_payment_id': 'pi_demo_12345',
                'amount_usd': 5000,
                'status': 'succeeded',
                'description': 'Annual Professional Plan',
                'paid_at': timezone.now() - timedelta(days=30),
            }
        )

        self.stdout.write(f'  Created subscription plans and payment records')
