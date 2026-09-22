from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import ServiceRecord, PredictiveAlert

class ServiceList(LoginRequiredMixin, ListView):
    model = ServiceRecord
    template_name = 'maintenance/list.html'
    context_object_name = 'services'
    ordering = ['-service_date']

class ServiceCreate(LoginRequiredMixin, CreateView):
    model = ServiceRecord
    fields = ['motorcycle', 'customer', 'mileage', 'description', 'parts_replaced',
              'next_due_mileage', 'next_due_date']
    template_name = 'maintenance/form.html'
    success_url = reverse_lazy('service-list')

    def form_valid(self, form):
        resp = super().form_valid(form)
        # auto-update bike mileage
        bike = self.object.motorcycle
        if self.object.mileage > bike.mileage:
            bike.mileage = self.object.mileage
            bike.save()
        return resp

class AlertList(LoginRequiredMixin, ListView):
    model = PredictiveAlert
    template_name = 'maintenance/alerts.html'
    context_object_name = 'alerts'
    queryset = PredictiveAlert.objects.filter(is_done=False).order_by('-created_at')
