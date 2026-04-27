from django.urls import path

from dashboards.views import AdminDashboardView, AnalyticsJsonView, DashboardRedirectView, UserDashboardView

app_name = "dashboards"

urlpatterns = [
    path("", DashboardRedirectView.as_view(), name="dashboard"),
    path("me/", UserDashboardView.as_view(), name="user_dashboard"),
    path("admin/", AdminDashboardView.as_view(), name="admin_dashboard"),
    path("api/analytics/", AnalyticsJsonView.as_view(), name="analytics_api"),
]
