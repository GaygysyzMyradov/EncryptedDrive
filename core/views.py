import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.db.models.functions import Lower
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View

# Create your views here.
from django.views.generic import ListView, CreateView, DetailView, DeleteView

from .forms import FileUploadForm, CreateFolderForm
from .models import Folder, File


class HomeListView(LoginRequiredMixin, ListView):
    model = Folder
    template_name = 'core/home.html'

    def get_queryset(self):
        query = Folder.objects.filter(folder_owner=self.request.user)
        sort_by = self.request.GET.get('sort')
        search_query = self.request.GET.get('q')
        if search_query:
            query = query.filter(name__icontains=search_query)
        if sort_by == 'name':
            query = query.annotate(lower_name=Lower('name')).order_by('lower_name')
        elif sort_by == 'date':
            query = query.order_by('-created_at')

        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CreateFolderForm()
        context['folders'] = self.get_queryset()
        return context

    def post(self, request, *args, **kwargs):
        form = CreateFolderForm(request.POST)
        if form.is_valid():
            new_folder = form.save(commit=False)
            new_folder.folder_owner = self.request.user
            new_folder.save()
            messages.success(request, 'Folder is Added')
            return redirect('home')
        else:
            messages.error(request, 'Please Add Valid Inputs.')
            return redirect('home')


class CreateFolderView(CreateView):
    model = Folder
    template_name = 'core/create_folder.html'
    fields = ['name']

    def form_valid(self, form):
        form.instance.folder_owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('home')


class FolderDeleteView(LoginRequiredMixin, DeleteView):
    model = Folder
    template_name = 'core/home.html'

    def get_object(self, queryset=None):
        return Folder.objects.get(slug=self.kwargs['slug'])

    def get_success_url(self):
        folder = self.get_object()
        message = f'You deleted the file {folder.name} successfully.'
        messages.success(self.request, message)
        return reverse_lazy('home')


class UserFolderDetailView(DetailView):
    model = Folder
    template_name = 'core/folder_files_detail.html'
    context_object_name = 'folder'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        folder = self.get_object()
        files_in_folder = File.objects.filter(folder=folder)

        sort_by = self.request.GET.get('sort')
        search_query = self.request.GET.get('q')
        if search_query:
            files_in_folder = files_in_folder.filter(name__icontains=search_query, folder=folder)

        if sort_by == 'latest':
            files_in_folder = files_in_folder.order_by('-created_at')
        elif sort_by == 'name':
            files_in_folder = files_in_folder.annotate(lower_name=Lower('name')).order_by('lower_name')

        context['files'] = files_in_folder
        context['form'] = FileUploadForm()
        return context


class FileUploadView(View):
    def get(self, request, folder_slug):
        folder = get_object_or_404(Folder, slug=folder_slug)
        form = FileUploadForm()
        return redirect(reverse('user_folder_detail', kwargs={'slug': folder.slug}))

    def post(self, request, folder_slug):
        folder = get_object_or_404(Folder, slug=folder_slug)
        form = FileUploadForm(request.POST, request.FILES)

        if form.is_valid():
            file_instance = form.save(commit=False)

            uploaded_file = request.FILES.get('file')
            file_instance.file_owner = request.user
            file_instance.folder = folder
            file_instance.decrypted = True
            encryption_key = Fernet.generate_key()
            fernet = Fernet(encryption_key)
            encrypted_data = fernet.encrypt(uploaded_file.read())
            file_instance.decryption_key = base64.urlsafe_b64encode(encryption_key).decode('utf-8')

            temp_file = ContentFile(encrypted_data)
            file_instance.file.save(uploaded_file.name, temp_file)

            file_instance.save()
            message = f' File  {file_instance.name} is Uploaded successfully.'
            messages.success(request, message)

            return redirect(reverse('user_folder_detail', kwargs={'slug': folder_slug}))
        else:
            return redirect(reverse('user_folder_detail', kwargs={'slug': folder_slug}))


class DecryptFileView(View):
    def get(self, request, file_slug):
        try:
            file_instance = get_object_or_404(File, slug=file_slug)
            encryption_key = base64.urlsafe_b64decode(file_instance.decryption_key.encode('utf-8'))
            fernet = Fernet(encryption_key)

            with open(file_instance.file.path, 'rb') as encrypted_file:
                encrypted_data = encrypted_file.read()
                decrypted_data = fernet.decrypt(encrypted_data)
            _, file_extension = os.path.splitext(file_instance.file.path)
            print(file_extension)
            response = HttpResponse(decrypted_data, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_instance.file.path)}"'

            return response

        except File.DoesNotExist:
            messages.error(request, 'File Not Found')

        except InvalidToken as e:
            messages.error(request, 'Invalid decryption key.')

        except Exception as e:
            messages.error(request, 'An error occurred during decryption.')

        return HttpResponse(status=500)



class DeleteFileView(View):
    def post(self, request, file_slug):
        try:
            file_obj = get_object_or_404(File, slug=file_slug)
            file_obj.file.delete()
            file_obj.delete()

            return JsonResponse({'success': 'File deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class FileDeleteView(LoginRequiredMixin, DeleteView):
    model = File
    template_name = 'core/folder_files_detail.html'

    def get_object(self, queryset=None):
        return File.objects.get(slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file_object = self.get_object()
        context['folder'] = file_object.folder
        return context

    def get_success_url(self):
        file_object = self.get_object()
        folder = file_object.folder
        message = f'You deleted the file {file_object.name} successfully.'
        messages.success(self.request, message)
        return reverse_lazy('user_folder_detail', kwargs={'slug': folder.slug})


# class UserFileDetailView(DetailView):
#     model = File
#     template_name = 'core/file_decrypted_page.html'
#     context_object_name = 'file'
#     slug_field = 'slug'
