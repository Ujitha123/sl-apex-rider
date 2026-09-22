from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import SparePart

class PartList(ListView):
    model = SparePart
    template_name = 'inventory/list.html'
    context_object_name = 'parts'

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        bike = self.request.GET.get('bike')
        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(part_number__icontains=q)
        if bike:
            qs = qs.filter(compatible_models__icontains=bike)
        return qs

class PartCreate(CreateView):
    model = SparePart
    fields = ['name', 'part_number', 'category', 'brand', 'compatible_models',
              'price', 'stock_qty', 'min_stock', 'description', 'service_interval_km']
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('part-list')
