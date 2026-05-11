from django.urls import path

from circulation.views import (
    BookRequestCreateView,
    BookRequestListView,
    BookRequestReviewView,
    BorrowingHistoryView,
    IssueBookView,
    NotificationListView,
    NotificationReadView,
    PaymentCheckoutView,
    PaymentConfirmView,
    PaymentListView,
    ReturnBookView,
)

app_name = "circulation"

urlpatterns = [
    path("books/<int:pk>/issue/", IssueBookView.as_view(), name="issue_book"),
    path("records/<int:pk>/return/", ReturnBookView.as_view(), name="return_book"),
    path("records/<int:record_pk>/pay/", PaymentCheckoutView.as_view(), name="pay_record_fine"),
    path("history/", BorrowingHistoryView.as_view(), name="history"),
    path("payments/", PaymentListView.as_view(), name="payments"),
    path("payments/<int:pk>/confirm/", PaymentConfirmView.as_view(), name="payment_confirm"),
    path("requests/", BookRequestListView.as_view(), name="requests"),
    path("requests/new/", BookRequestCreateView.as_view(), name="request_new"),
    path("requests/new/book/<int:book_pk>/", BookRequestCreateView.as_view(), name="request_book"),
    path("requests/<int:pk>/review/", BookRequestReviewView.as_view(), name="request_review"),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("notifications/read/", NotificationReadView.as_view(), name="notifications_read_all"),
    path("notifications/<int:pk>/read/", NotificationReadView.as_view(), name="notification_read"),
]
