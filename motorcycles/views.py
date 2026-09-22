from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from .models import Motorcycle
from inventory.models import SparePart
from maintenance.models import generate_predictions

class BikeList(ListView):
    model = Motorcycle
    template_name = 'motorcycles/list.html'
    context_object_name = 'bikes'

class BikeCreate(CreateView):
    model = Motorcycle
    fields = ['customer', 'brand', 'model', 'year', 'plate_no', 'mileage']
    template_name = 'motorcycles/form.html'
    success_url = reverse_lazy('bike-list')

class BikeDetail(DetailView):
    model = Motorcycle
    template_name = 'motorcycles/detail.html'
    context_object_name = 'bike'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        bike = self.object
        # Compatibility recommendations (Objective 4)
        ctx['compatible_parts'] = SparePart.objects.filter(
            compatible_models__icontains=bike.model)[:10]
        # Predictive maintenance (Objective 4)
        ctx['alerts'] = generate_predictions(bike)
        ctx['services'] = bike.services.order_by('-service_date')[:10]
        return ctx
