import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from accounts.permissions import LibraryStaffRequiredMixin, can_manage_library
from catalog.models import Book, BookReview
from circulation.models import BookRequest, BorrowRecord, Notification, PaymentTransaction


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request):
        if can_manage_library(request.user):
            return redirect("dashboards:admin_dashboard")
        return redirect("dashboards:user_dashboard")


class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboards/user_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        active_records = BorrowRecord.objects.select_related("book").filter(
            user=user,
            status=BorrowRecord.Status.BORROWED,
            return_date__isnull=True,
        )
        history = BorrowRecord.objects.select_related("book").filter(user=user)[:8]
        requests = BookRequest.objects.select_related("book").filter(user=user)[:5]
        notifications = Notification.objects.filter(user=user)[:6]

        borrowed_genres = list(
            BorrowRecord.objects.filter(user=user).values_list("book__genre", flat=True).distinct()
        )
        borrowed_books = BorrowRecord.objects.filter(user=user).values_list("book_id", flat=True)
        recommendation_query = Book.objects.with_popularity().filter(available_stock__gt=0).exclude(
            pk__in=borrowed_books
        )
        if borrowed_genres:
            recommendation_query = recommendation_query.filter(genre__in=borrowed_genres)
        recommendations = recommendation_query.order_by("-issue_count", "title")[:6]
        if not recommendations:
            recommendations = Book.objects.with_popularity().filter(available_stock__gt=0).order_by(
                "-issue_count",
                "title",
            )[:6]

        due_records = [
            record
            for record in BorrowRecord.objects.select_related("book").filter(user=user)
            if record.fine_due > 0
        ]
        pending_fines = sum((record.fine_due for record in due_records), Decimal("0.00"))
        context.update(
            {
                "active_records": active_records,
                "due_records": due_records,
                "history": history,
                "requests": requests,
                "notifications": notifications,
                "recommendations": recommendations,
                "pending_fines": pending_fines,
                "recent_payments": PaymentTransaction.objects.filter(user=user)[:5],
            }
        )
        return context


class AdminDashboardView(LoginRequiredMixin, LibraryStaffRequiredMixin, TemplateView):
    template_name = "dashboards/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_records = BorrowRecord.objects.select_related("book", "user").filter(
            status=BorrowRecord.Status.BORROWED,
            return_date__isnull=True,
        )
        overdue_records = [record for record in active_records if record.is_overdue]
        most_borrowed = Book.objects.with_popularity().order_by("-issue_count", "title")[:6]
        active_users = (
            get_user_model()
            .objects.annotate(active_loans=Count("borrow_records", filter=Q(borrow_records__status="BORROWED")))
            .filter(active_loans__gt=0)
            .order_by("-active_loans", "username")[:6]
        )
        genre_counts = list(Book.objects.values("genre").annotate(total=Count("id")).order_by("genre"))
        request_counts = list(BookRequest.objects.values("status").annotate(total=Count("id")).order_by("status"))

        context.update(
            {
                "stats": {
                    "books": Book.objects.count(),
                    "members": get_user_model().objects.filter(is_active=True).count(),
                    "active_loans": active_records.count(),
                    "overdue": len(overdue_records),
                    "pending_requests": BookRequest.objects.filter(status=BookRequest.Status.PENDING).count(),
                    "reviews": BookReview.objects.filter(is_public=True).count(),
                    "pending_payments": PaymentTransaction.objects.filter(
                        status=PaymentTransaction.Status.PENDING
                    ).count(),
                    "collected_dues": sum(
                        (
                            payment.amount
                            for payment in PaymentTransaction.objects.filter(status=PaymentTransaction.Status.PAID)
                        ),
                        Decimal("0.00"),
                    ),
                    "fine_exposure": sum((record.fine_due for record in overdue_records), Decimal("0.00")),
                },
                "active_records": active_records[:8],
                "overdue_records": overdue_records[:8],
                "pending_requests": BookRequest.objects.select_related("book", "user").filter(
                    status=BookRequest.Status.PENDING
                )[:8],
                "most_borrowed": most_borrowed,
                "active_users": active_users,
                "pending_payments": PaymentTransaction.objects.select_related("user", "borrow_record__book").filter(
                    status=PaymentTransaction.Status.PENDING
                )[:8],
                "genre_counts_json": json.dumps(genre_counts),
                "request_counts_json": json.dumps(request_counts),
            }
        )
        return context


class AnalyticsJsonView(LoginRequiredMixin, LibraryStaffRequiredMixin, View):
    def get(self, request):
        return JsonResponse(
            {
                "books": Book.objects.count(),
                "active_loans": BorrowRecord.objects.filter(status=BorrowRecord.Status.BORROWED).count(),
                "pending_requests": BookRequest.objects.filter(status=BookRequest.Status.PENDING).count(),
                "reviews": BookReview.objects.filter(is_public=True).count(),
                "pending_payments": PaymentTransaction.objects.filter(status=PaymentTransaction.Status.PENDING).count(),
                "most_borrowed": [
                    {"title": book.title, "issues": book.issue_count}
                    for book in Book.objects.with_popularity().order_by("-issue_count", "title")[:10]
                ],
            }
        )
