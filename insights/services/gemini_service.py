import os
import json
import google.generativeai as genai
from django.conf import settings
from finances.models import RapportFinancier, Transaction
from voyages.models import Voyage
from reservations.models import Reservation
from insights.models import FinancialInsight, TravelTrend, AIRecommendation

class GeminiService:
    def __init__(self):
        api_key = settings.GEMINI_API_KEY
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def analyze_financial_report(self, rapport_id):
        """Analyser un rapport financier et générer des insights"""
        try:
            rapport = RapportFinancier.objects.get(id=rapport_id)
            
            # Récupérer les données contextuelles
            transactions = Transaction.objects.filter(
                date__range=[rapport.date_debut, rapport.date_fin]
            ).values()
            
            # Préparer les données pour l'analyse
            financial_data = {
                "rapport": {
                    "titre": rapport.titre,
                    "periode": rapport.periode,
                    "date_debut": str(rapport.date_debut),
                    "date_fin": str(rapport.date_fin),
                    "revenus_totaux": float(rapport.revenus_totaux),
                    "depenses_totales": float(rapport.depenses_totales),
                    "benefice_net": float(rapport.benefice_net),
                    "details": rapport.details
                },
                "transactions": list(transactions)
            }
            
            # Créer le prompt pour Gemini
            prompt = f"""
            En tant qu'analyste financier pour une agence de voyage, analyse ces données financières et fournit 3 insights importants:
            
            {json.dumps(financial_data, indent=2)}
            
            Pour chaque insight, inclut:
            1. Un titre concis
            2. Une description détaillée
            3. Le type d'insight (tendance, recommandation, alerte, opportunité)
            4. La priorité (basse, moyenne, haute, critique)
            5. Des actions recommandées
            6. Des métriques clés
            
            Réponds uniquement au format JSON comme ceci:
            {{
                "insights": [
                    {{
                        "titre": "Titre de l'insight",
                        "description": "Description détaillée",
                        "type": "type_insight",
                        "priorite": "priorite_insight",
                        "actions_recommandees": ["action1", "action2"],
                        "metriques": {{"metrique1": valeur1, "metrique2": valeur2}}
                    }}
                ]
            }}
            """
            
            # Appeler l'API Gemini
            response = self.model.generate_content(prompt)
            
            # Extraire et parser la réponse JSON
            try:
                response_text = response.text
                insights_data = json.loads(response_text)
                
                # Sauvegarder les insights dans la base de données
                created_insights = []
                for insight_data in insights_data.get('insights', []):
                    insight = FinancialInsight.objects.create(
                        titre=insight_data.get('titre'),
                        description=insight_data.get('description'),
                        type=insight_data.get('type'),
                        priorite=insight_data.get('priorite'),
                        rapport=rapport,
                        actions_recommandees=insight_data.get('actions_recommandees', []),
                        metriques=insight_data.get('metriques', {})
                    )
                    created_insights.append(insight)
                
                return created_insights
            except json.JSONDecodeError:
                print("Erreur de décodage JSON:", response.text)
                return []
                
        except RapportFinancier.DoesNotExist:
            print(f"Rapport financier avec ID {rapport_id} non trouvé")
            return []
        except Exception as e:
            print(f"Erreur lors de l'analyse financière: {str(e)}")
            return []
    
    def analyze_travel_trends(self):
        """Analyser les tendances de voyage et générer des recommandations"""
        try:
            # Récupérer les données des voyages et réservations
            voyages = Voyage.objects.all().values()
            reservations = Reservation.objects.all().values()
            
            # Préparer les données pour l'analyse
            travel_data = {
                "voyages": list(voyages),
                "reservations": list(reservations)
            }
            
            # Créer le prompt pour Gemini
            prompt = f"""
            En tant qu'analyste de données pour une agence de voyage, analyse ces données de voyages et réservations:
            
            {json.dumps(travel_data, indent=2)}
            
            Identifie les 3 principales tendances de destinations et fournit des recommandations pour augmenter les ventes.
            
            Pour chaque tendance, inclut:
            1. La destination
            2. La variation en pourcentage
            3. Si c'est une tendance à la hausse ou à la baisse
            4. Les facteurs possibles
            5. Une recommandation spécifique de voyage à créer pour capitaliser sur cette tendance
            
            Réponds uniquement au format JSON comme ceci:
            {{
                "tendances": [
                    {{
                        "destination": "Nom de la destination",
                        "variation_pourcentage": 15.5,
                        "est_en_hausse": true,
                        "facteurs": ["facteur1", "facteur2"],
                        "recommandation": {{
                            "titre": "Titre du voyage recommandé",
                            "description": "Description détaillée",
                            "impact_estime": 10.5,
                            "details": {{"duree": 7, "prix_suggere": 1200, "activites": ["activite1", "activite2"]}}
                        }}
                    }}
                ]
            }}
            """
            
            # Appeler l'API Gemini
            response = self.model.generate_content(prompt)
            
            # Extraire et parser la réponse JSON
            try:
                response_text = response.text
                trends_data = json.loads(response_text)
                
                # Sauvegarder les tendances et recommandations dans la base de données
                created_trends = []
                for trend_data in trends_data.get('tendances', []):
                    # Créer la tendance
                    trend = TravelTrend.objects.create(
                        destination=trend_data.get('destination'),
                        variation_pourcentage=trend_data.get('variation_pourcentage'),
                        periode_debut="2023-01-01",  # À adapter selon vos besoins
                        periode_fin="2023-12-31",    # À adapter selon vos besoins
                        nombre_reservations=0,       # À calculer à partir des données réelles
                        revenu_total=0,              # À calculer à partir des données réelles
                        est_en_hausse=trend_data.get('est_en_hausse', True),
                        facteurs=trend_data.get('facteurs', [])
                    )
                    
                    # Créer la recommandation associée
                    if 'recommandation' in trend_data:
                        rec_data = trend_data['recommandation']
                        recommendation = AIRecommendation.objects.create(
                            titre=rec_data.get('titre'),
                            description=rec_data.get('description'),
                            impact_estime=rec_data.get('impact_estime', 0),
                            details=rec_data.get('details', {})
                        )
                    
                    created_trends.append(trend)
                
                return created_trends
            except json.JSONDecodeError:
                print("Erreur de décodage JSON:", response.text)
                return []
                
        except Exception as e:
            print(f"Erreur lors de l'analyse des tendances: {str(e)}")
            return []