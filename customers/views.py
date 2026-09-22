from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Customer

class CustomerList(ListView):
    model = Customer
    template_name = 'customers/list.html'
    context_object_name = 'customers'

class CustomerCreate(CreateView):
    model = Customer
    fields = ['name', 'phone', 'email', 'address']
    template_name = 'customers/form.html'
    success_url = reverse_lazy('customer-list')

class CustomerUpdate(UpdateView):
    model = Customer
    fields = ['name', 'phone', 'email', 'address']
    template_name = 'customers/form.html'
    success_url = reverse_lazy('customer-list')
