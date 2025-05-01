from typing import Dict, Any, List
import pandas as pd
from django.db.models import Sum, Avg, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta

class FinancialAnalyzer:
    """Service d'analyse des données financières"""
    
    def __init__(self, financial_data_model, destination_financial_data_model):
        self.financial_data_model = financial_data_model
        self.destination_financial_data_model = destination_financial_data_model
    
    def get_financial_overview(self, year: int = None, month: int = None) -> Dict[str, Any]:
        """
        Récupère une vue d'ensemble des données financières
        
        Args:
            year: Année à analyser (par défaut: année en cours)
            month: Mois à analyser (optionnel)
            
        Returns:
            Dict contenant les données financières agrégées
        """
        if not year:
            year = datetime.now().year
            
        # Filtrer les données par année et mois si spécifié
        queryset = self.financial_data_model.objects.filter(period__year=year)
        if month:
            queryset = queryset.filter(period__month=month)
            
        # Calculer les totaux
        totals = queryset.aggregate(
            total_revenue=Sum('revenue'),
            total_costs=Sum('costs'),
            total_margin=Sum(F('revenue') - F('costs'))
        )
        
        # Calculer le taux de marge moyen
        if totals['total_revenue']:
            margin_rate = (totals['total_margin'] / totals['total_revenue']) * 100
        else:
            margin_rate = 0
            
        # Récupérer les données de l'année précédente pour comparaison
        prev_year = year - 1
        prev_queryset = self.financial_data_model.objects.filter(period__year=prev_year)
        if month:
            prev_queryset = prev_queryset.filter(period__month=month)
            
        prev_totals = prev_queryset.aggregate(
            prev_total_revenue=Sum('revenue'),
            prev_total_costs=Sum('costs'),
            prev_total_margin=Sum(F('revenue') - F('costs'))
        )
        
        # Calculer les variations en pourcentage
        changes = {}
        for key in ['revenue', 'costs', 'margin']:
            current = totals[f'total_{key}'] or 0
            previous = prev_totals[f'prev_total_{key}'] or 0
            
            if previous:
                changes[f'{key}_change'] = ((current - previous) / previous) * 100
            else:
                changes[f'{key}_change'] = 0
        
        # Récupérer les données mensuelles pour l'année en cours
        monthly_data = self.financial_data_model.objects.filter(
            period__year=year,
            period__period_type='month'
        ).values(
            'period__month'
        ).annotate(
            revenue=Sum('revenue'),
            costs=Sum('costs'),
            margin=Sum(F('revenue') - F('costs'))
        ).order_by('period__month')
        
        # Convertir en liste pour le JSON
        monthly_data_list = list(monthly_data)
        
        # Récupérer les données par destination
        destination_data = self.destination_financial_data_model.objects.filter(
            period__year=year
        ).values(
            'destination__name'
        ).annotate(
            revenue=Sum('revenue'),
            costs=Sum('costs'),
            margin=Sum(F('revenue') - F('costs'))
        ).order_by('-revenue')[:10]  # Top 10 destinations
        
        # Convertir en liste pour le JSON
        destination_data_list = list(destination_data)
        
        # Assembler les résultats
        result = {
            'period': {
                'year': year,
                'month': month
            },
            'totals': {
                'revenue': float(totals['total_revenue'] or 0),
                'costs': float(totals['total_costs'] or 0),
                'margin': float(totals['total_margin'] or 0),
                'margin_rate': float(margin_rate)
            },
            'changes': {
                'revenue_change': float(changes['revenue_change']),
                'costs_change': float(changes['costs_change']),
                'margin_change': float(changes['margin_change'])
            },
            'monthly_data': [
                {
                    'month': item['period__month'],
                    'revenue': float(item['revenue']),
                    'costs': float(item['costs']),
                    'margin': float(item['margin'])
                } for item in monthly_data_list
            ],
            'destination_data': [
                {
                    'destination': item['destination__name'],
                    'revenue': float(item['revenue']),
                    'costs': float(item['costs']),
                    'margin': float(item['margin'])
                } for item in destination_data_list
            ]
        }
        
        return result