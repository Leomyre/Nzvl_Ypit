from rest_framework import serializers
from .models import Destination, Voyage, ProgrammeJour, Inclusion, Activite, Avis, HistoriqueConsultation, TypeVoyage

class DestinationSerializer(serializers.ModelSerializer):
    nombre_voyages = serializers.SerializerMethodField()
    voyages_ids = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = ['id', 'nom', 'pays', 'description', 'latitude', 'longitude', 
                 'image', 'created_at', 'updated_at',
                 'nombre_voyages', 'voyages_ids']
        read_only_fields = ('created_at', 'updated_at')

    def get_nombre_voyages(self, obj):
        return obj.voyages.count()  # Utilise le related_name si défini
    
    def get_voyages_ids(self, obj):
        voyages = obj.voyages.all().values('id', 'titre', 'prix', 'niveau_confort', 'images')
        for voyage in voyages:
            voyage['destination_nom'] = obj.nom  # Ajoute le nom de la destination
        return list(voyages)

    # Validation supplémentaire pour la création
    def validate(self, data):
        if self.instance is None:  # Création seulement
            exists = Destination.objects.filter(
                nom__iexact=data.get('nom'),
                pays__iexact=data.get('pays')
            ).exists()
            if exists:
                raise serializers.ValidationError(
                    "Cette destination existe déjà."
                )
        return data

class ProgrammeJourSerializer(serializers.ModelSerializer):
    voyage = serializers.PrimaryKeyRelatedField(queryset=Voyage.objects.all(), write_only=True)
    class Meta:
        model = ProgrammeJour
        fields = '__all__'

class InclusionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inclusion
        fields = '__all__'

class TypeVoyageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeVoyage
        fields = ['id', 'nom']

class VoyageSerializer(serializers.ModelSerializer):
    destination = serializers.PrimaryKeyRelatedField(queryset=Destination.objects.all())
    destination_nom = serializers.SerializerMethodField()
    type_voyage = TypeVoyageSerializer(read_only=True)

    class Meta:
        model = Voyage
        fields = [
            'id', 'titre', 'description', 'ville_depart', 'destination', 'destination_nom',
            'prix', 'niveau_confort', 'est_populaire', 'est_recommande', 'images', 'type_voyage'
        ]

    def validate_destination(self, value):
        if not value:
            raise serializers.ValidationError("La destination est obligatoire.")
        return value


    def get_destination_nom(self, obj):
        """
        Récupère le nom de la destination liée à ce voyage.
        """
        return obj.destination.nom  # Remplacez 'nom' par le champ qui contient le nom de la destination dans votre modèle


class VoyageDetailSerializer(serializers.ModelSerializer):
    destination = DestinationSerializer(read_only=True)
    programmes_jour = ProgrammeJourSerializer(many=True, read_only=True)
    inclusions = InclusionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Voyage
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class ActiviteSerializer(serializers.ModelSerializer):
    destination = serializers.StringRelatedField()
    
    class Meta:
        model = Activite
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class AvisSerializer(serializers.ModelSerializer):
    utilisateur = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Avis
        fields = '__all__'
        read_only_fields = ('date_creation', 'date_modification')
        extra_kwargs = {
            'voyage': {'required': True}
        }
    
    def validate_note(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("La note doit être entre 1 et 5.")
        return value

class CreateAvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avis
        fields = ['note', 'commentaire']

class HistoriqueConsultationSerializer(serializers.ModelSerializer):
    titre = serializers.CharField(source='voyage.titre', read_only=True)
    destination_nom = serializers.CharField(source='voyage.destination', read_only=True)
    prix = serializers.DecimalField(source='voyage.prix', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = HistoriqueConsultation
        fields = ['id', 'titre', 'destination_nom', 'date_consultation', 'prix', 'voyage']
