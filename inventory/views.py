from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import SparePart, Category

class PartList(LoginRequiredMixin, ListView):
    model = SparePart
    template_name = 'inventory/list.html'
    context_object_name = 'parts'

    def get_queryset(self):
        qs = super().get_queryset().select_related('category').order_by('category__name', 'name')
        q = self.request.GET.get('q')
        bike = self.request.GET.get('bike')
        cat = self.request.GET.get('cat')
        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(part_number__icontains=q)
        if bike:
            qs = qs.filter(compatible_models__icontains=bike)
        if cat:
            qs = qs.filter(category__name=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.order_by('name')
        ctx['active_cat'] = self.request.GET.get('cat', '')
        return ctx

class PartCreate(LoginRequiredMixin, CreateView):
    model = SparePart
    fields = ['name', 'part_number', 'category', 'brand', 'compatible_models',
              'price', 'negotiable', 'stock_qty', 'min_stock', 'description', 'service_interval_km']
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('part-list')
