from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.permissions import LibraryStaffRequiredMixin, can_manage_library
from catalog.models import Book
from circulation.forms import BookRequestForm, BorrowBookForm, RequestReviewForm
from circulation.models import BookRequest, BorrowRecord, Notification, PaymentTransaction


class IssueBookView(LoginRequiredMixin, View):
    def post(self, request, pk):
        form = BorrowBookForm(request.POST, user=request.user)
        book = get_object_or_404(Book, pk=pk)
        if not form.is_valid():
            messages.error(request, "Please review the checkout form.")
            return redirect(book.get_absolute_url())

        checkout_user = form.checkout_user()
        if checkout_user != request.user and not can_manage_library(request.user):
            raise PermissionDenied("Only library staff can issue books to another member.")

        try:
            with transaction.atomic():
                locked_book = Book.objects.select_for_update().get(pk=book.pk)
                locked_book.issue_copy()
                BorrowRecord.objects.create(
                    user=checkout_user,
                    book=locked_book,
                    issued_by=request.user if can_manage_library(request.user) else None,
                    due_date=form.cleaned_data["due_date"],
                    notes=form.cleaned_data.get("notes", ""),
                )
        except IntegrityError:
            messages.warning(request, "This member already has an active checkout for that book.")
        except Exception as exc:
            messages.error(request, str(exc))
        else:
            Notification.objects.create(
                user=checkout_user,
                kind=Notification.Kind.INFO,
                message=f"{book.title} is checked out until {form.cleaned_data['due_date']}.",
                link=book.get_absolute_url(),
            )
            messages.success(request, f"{book.title} checked out successfully.")
        return redirect(book.get_absolute_url())


class ReturnBookView(LoginRequiredMixin, View):
    def post(self, request, pk):
        record = get_object_or_404(
            BorrowRecord.objects.select_related("book", "user"),
            pk=pk,
            status=BorrowRecord.Status.BORROWED,
            return_date__isnull=True,
        )
        if record.user != request.user and not can_manage_library(request.user):
            raise PermissionDenied("You cannot return another member's checkout.")
        with transaction.atomic():
            record.return_book()
        if record.fine_amount:
            messages.warning(request, f"Returned with a fine of ₹{record.fine_amount}.")
        else:
            messages.success(request, "Book returned. Thank you.")
        Notification.objects.create(
            user=record.user,
            kind=Notification.Kind.RETURN,
            message=f"{record.book.title} has been returned.",
            link=record.book.get_absolute_url(),
        )
        return redirect(request.POST.get("next") or "circulation:history")


class BorrowingHistoryView(LoginRequiredMixin, ListView):
    model = BorrowRecord
    template_name = "circulation/history.html"
    context_object_name = "records"
    paginate_by = 12

    def get_queryset(self):
        queryset = BorrowRecord.objects.select_related("book", "user", "issued_by")
        if can_manage_library(self.request.user):
            return queryset
        return queryset.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["querystring"] = query_params.urlencode()
        return context


class PaymentListView(LoginRequiredMixin, ListView):
    model = PaymentTransaction
    template_name = "circulation/payment_list.html"
    context_object_name = "payments"
    paginate_by = 12

    def get_queryset(self):
        queryset = PaymentTransaction.objects.select_related("user", "borrow_record", "borrow_record__book")
        if can_manage_library(self.request.user):
            return queryset
        return queryset.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["querystring"] = query_params.urlencode()
        return context


class PaymentCheckoutView(LoginRequiredMixin, DetailView):
    model = PaymentTransaction
    template_name = "circulation/payment_checkout.html"
    context_object_name = "payment"

    def dispatch(self, request, *args, **kwargs):
        self.borrow_record = get_object_or_404(
            BorrowRecord.objects.select_related("book", "user"),
            pk=kwargs["record_pk"],
        )
        if self.borrow_record.user != request.user and not can_manage_library(request.user):
            raise PermissionDenied("You cannot pay dues for another member.")
        if self.borrow_record.fine_due <= 0:
            messages.info(request, "There are no outstanding dues for that record.")
            return redirect("circulation:history")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        payment = PaymentTransaction.objects.filter(
            borrow_record=self.borrow_record,
            status=PaymentTransaction.Status.PENDING,
        ).first()
        if payment:
            return payment
        return PaymentTransaction.objects.create(
            user=self.borrow_record.user,
            borrow_record=self.borrow_record,
            amount=self.borrow_record.fine_due,
            reference=f"BKLY-{uuid4().hex[:10].upper()}",
            note=f"Fine for {self.borrow_record.book.title}",
        )


class PaymentConfirmView(LoginRequiredMixin, View):
    def post(self, request, pk):
        payment = get_object_or_404(
            PaymentTransaction.objects.select_related("borrow_record", "borrow_record__book", "user"),
            pk=pk,
        )
        if payment.user != request.user and not can_manage_library(request.user):
            raise PermissionDenied("You cannot confirm another member's payment.")
        if payment.status != PaymentTransaction.Status.PAID:
            payment.mark_paid()
            Notification.objects.create(
                user=payment.user,
                kind=Notification.Kind.PAYMENT,
                message=f"Payment {payment.reference} for ₹{payment.amount} was recorded.",
                link=reverse("circulation:payments"),
            )
            messages.success(request, "Payment recorded and dues marked as paid.")
        return redirect("circulation:payments")


class BookRequestCreateView(LoginRequiredMixin, CreateView):
    model = BookRequest
    form_class = BookRequestForm
    template_name = "circulation/request_form.html"
    success_url = reverse_lazy("circulation:requests")

    def dispatch(self, request, *args, **kwargs):
        self.book = None
        book_pk = kwargs.get("book_pk") or request.GET.get("book")
        if book_pk:
            self.book = get_object_or_404(Book, pk=book_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["book"] = self.book
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.book = self.book
        if self.book:
            form.instance.requested_title = self.book.title
            form.instance.requested_author = self.book.author
            form.instance.genre = self.book.genre
        messages.success(self.request, "Request submitted for review.")
        return super().form_valid(form)


class BookRequestListView(LoginRequiredMixin, ListView):
    model = BookRequest
    template_name = "circulation/request_list.html"
    context_object_name = "requests"
    paginate_by = 12

    def get_queryset(self):
        queryset = BookRequest.objects.select_related("book", "user", "reviewed_by")
        if can_manage_library(self.request.user):
            return queryset
        return queryset.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["querystring"] = query_params.urlencode()
        return context


class BookRequestReviewView(LoginRequiredMixin, LibraryStaffRequiredMixin, UpdateView):
    model = BookRequest
    form_class = RequestReviewForm
    template_name = "circulation/request_review.html"
    success_url = reverse_lazy("circulation:requests")

    def form_valid(self, form):
        form.instance.reviewed_by = self.request.user
        form.instance.reviewed_at = timezone.now()
        response = super().form_valid(form)
        Notification.objects.create(
            user=self.object.user,
            kind=Notification.Kind.REQUEST,
            message=f"Your request for {self.object.display_title} is {self.object.get_status_display().lower()}.",
            link=reverse("circulation:requests"),
        )
        messages.success(self.request, "Request review saved.")
        return response


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "circulation/notifications.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["querystring"] = query_params.urlencode()
        return context


class NotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk=None):
        queryset = Notification.objects.filter(user=request.user)
        if pk:
            queryset = queryset.filter(pk=pk)
        queryset.update(is_read=True)
        return redirect(request.POST.get("next") or "circulation:notifications")
