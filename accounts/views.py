from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from accounts.forms import ProfileUpdateForm, RegistrationForm, UserUpdateForm


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("dashboards:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Your Bookly library card is ready.")
        return response


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_form"] = UserUpdateForm(instance=self.request.user)
        context["profile_form"] = ProfileUpdateForm(instance=self.request.user.profile)
        return context

    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user.profile,
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
        else:
            messages.error(request, "Please fix the highlighted profile fields.")
        return self.get(request, *args, **kwargs)
