from typing import Dict, Any, List
import pandas as pd
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta

class TrendAnalyzer:
    """Service d'analyse des tendances de réservation"""
    
    def __init__(self, reservation_model, destination_model):
        self.reservation_model = reservation_model
        self.destination_model = destination_model
    
    def get_reservation_trends(self, months_back: int = 6) -> Dict[str, Any]:
        """
        Analyse les tendances de réservation sur les derniers mois
        
        Args:
            months_back: Nombre de mois à analyser en arrière
            
        Returns:
            Dict contenant les tendances de réservation
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months_back)
        
        # Réservations par mois
        monthly_reservations = self.reservation_model.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            total_value=Sum('total_price')
        ).order_by('month')
        
        # Convertir en liste pour le JSON
        monthly_data = [
            {
                'month': item['month'].strftime('%Y-%m'),
                'count': item['count'],
                'total_value': float(item['total_value'])
            } for item in monthly_reservations
        ]
        
        # Destinations les plus populaires
        popular_destinations = self.reservation_model.objects.filter(
            created_at__gte=start_date
        ).values(
            'destination__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]  # Top 10
        
        # Calculer les variations entre le mois dernier et le mois précédent
        if len(monthly_data) >= 2:
            current_month = monthly_data[-1]
            previous_month = monthly_data[-2]
            
            count_change = ((current_month['count'] - previous_month['count']) / previous_month['count']) * 100 if previous_month['count'] else 0
            value_change = ((current_month['total_value'] - previous_month['total_value']) / previous_month['total_value']) * 100 if previous_month['total_value'] else 0
        else:
            count_change = 0
            value_change = 0
        
        # Destinations en croissance (comparaison avec le mois précédent)
        current_month_start = end_date.replace(day=1)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        current_month_destinations = self.reservation_model.objects.filter(
            created_at__gte=current_month_start
        ).values(
            'destination__name'
        ).annotate(
            count=Count('id')
        )
        
        previous_month_destinations = self.reservation_model.objects.filter(
            created_at__gte=previous_month_start,
            created_at__lt=current_month_start
        ).values(
            'destination__name'
        ).annotate(
            count=Count('id')
        )
        
        # Convertir en dictionnaires pour faciliter la comparaison
        current_dict = {item['destination__name']: item['count'] for item in current_month_destinations}
        previous_dict = {item['destination__name']: item['count'] for item in previous_month_destinations}
        
        # Calculer les destinations avec la plus forte croissance
        growth_destinations = []
        for dest, count in current_dict.items():
            prev_count = previous_dict.get(dest, 0)
            if prev_count > 0:
                growth = ((count - prev_count) / prev_count) * 100
                growth_destinations.append({
                    'destination': dest,
                    'current_count': count,
                    'previous_count': prev_count,
                    'growth': growth
                })
        
        # Trier par croissance
        growth_destinations.sort(key=lambda x: x['growth'], reverse=True)
        
        # Assembler les résultats
        result = {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'months_analyzed': months_back
            },
            'monthly_trends': monthly_data,
            'current_month_changes': {
                'reservation_count_change': count_change,
                'reservation_value_change': value_change
            },
            'popular_destinations': [
                {
                    'destination': item['destination__name'],
                    'reservation_count': item['count']
                } for item in popular_destinations
            ],
            'growing_destinations': growth_destinations[:5]  # Top 5 en croissance
        }
        
        return result
    
    def get_seasonal_patterns(self) -> Dict[str, Any]:
        """
        Analyse les tendances saisonnières sur plusieurs années
        
        Returns:
            Dict contenant les tendances saisonnières
        """
        # Analyser les 3 dernières années
        end_year = datetime.now().year
        start_year = end_year - 3
        
        # Réservations par mois pour chaque année
        seasonal_data = []
        
        for year in range(start_year, end_year + 1):
            year_start = datetime(year, 1, 1)
            year_end = datetime(year, 12, 31)
            
            monthly_data = self.reservation_model.objects.filter(
                created_at__gte=year_start,
                created_at__lte=year_end
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')
            
            year_data = {
                'year': year,
                'monthly_data': [
                    {
                        'month': item['month'].month,
                        'count': item['count']
                    } for item in monthly_data
                ]
            }
            
            seasonal_data.append(year_data)
        
        # Destinations populaires par saison
        seasons = [
            {'name': 'Hiver', 'months': [12, 1, 2]},
            {'name': 'Printemps', 'months': [3, 4, 5]},
            {'name': 'Été', 'months': [6, 7, 8]},
            {'name': 'Automne', 'months': [9, 10, 11]}
        ]
        
        seasonal_destinations = []
        
        for season in seasons:
            # Créer un filtre pour les mois de la saison
            month_filter = Q()
            for month in season['months']:
                month_filter |= Q(created_at__month=month)
            
            # Destinations populaires pour cette saison
            popular_in_season = self.reservation_model.objects.filter(
                month_filter
            ).values(
                'destination__name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5]  # Top 5
            
            season_data = {
                'season': season['name'],
                'popular_destinations': [
                    {
                        'destination': item['destination__name'],
                        'count': item['count']
                    } for item in popular_in_season
                ]
            }
            
            seasonal_destinations.append(season_data)
        
        # Assembler les résultats
        result = {
            'years_analyzed': list(range(start_year, end_year + 1)),
            'seasonal_trends': seasonal_data,
            'seasonal_destinations': seasonal_destinations
        }
        
        return result