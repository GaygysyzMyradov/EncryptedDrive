from allauth.account.views import SignupView
from django.contrib.auth import logout
from django.shortcuts import render, redirect

from accounts.forms import CreateUserForm


class SignUpView(SignupView):

    template_name = 'account/signup.html'
    form_class = CreateUserForm

    def get(self, request, *args, **kwargs):
        # Use RequestContext instead of render_to_response from 3.0
        return render(request, self.template_name, {'form': self.form_class})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            return redirect('account_login')
        return render(request, self.template_name, {'form': form})

def logout_view(request):
    logout(request)
    return redirect("/")
