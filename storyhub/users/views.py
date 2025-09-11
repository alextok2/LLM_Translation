from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.urls import reverse_lazy
from django.views.generic import FormView
from .forms import SignUpForm

class SignupView(FormView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("translator_dashboard")  # или на каталог, если не переводчик

    def form_valid(self, form):
        user = form.save()
        user.email = form.cleaned_data.get("email", "")
        user.save(update_fields=["email"])

        # Назначаем роль(и)
        reader, _ = Group.objects.get_or_create(name="reader")
        user.groups.add(reader)

        if form.cleaned_data.get("as_translator"):
            translator, _ = Group.objects.get_or_create(name="translator")
            user.groups.add(translator)

        login(self.request, user)
        return super().form_valid(form)