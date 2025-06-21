from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Job, JobCategory, JobProposal

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class JobCategorySerializer(serializers.ModelSerializer):
    """Serializer for JobCategory model."""
    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

class JobListSerializer(serializers.ModelSerializer):
    """Serializer for listing jobs (lightweight version)."""
    client = UserSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)
    category = JobCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=JobCategory.objects.all(),
        source='category',
        write_only=True
    )
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'slug', 'description', 'status', 'budget', 'deadline',
            'created_at', 'updated_at', 'client', 'freelancer', 'category', 'category_id'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'client', 'freelancer']

class JobDetailSerializer(JobListSerializer):
    """Detailed serializer for Job model."""
    class Meta(JobListSerializer.Meta):
        fields = JobListSerializer.Meta.fields + [
            'requirements', 'skills_required', 'attachments', 'is_featured',
            'views_count', 'proposals_count', 'is_remote'
        ]

class JobProposalSerializer(serializers.ModelSerializer):
    """Serializer for JobProposal model."""
    freelancer = UserSerializer(read_only=True)
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    
    class Meta:
        model = JobProposal
        fields = [
            'id', 'job', 'freelancer', 'cover_letter', 'bid_amount',
            'estimated_days', 'status', 'submitted_at', 'accepted_at', 'rejected_at'
        ]
        read_only_fields = [
            'id', 'freelancer', 'status', 'submitted_at',
            'accepted_at', 'rejected_at'
        ]
    
    def create(self, validated_data):
        """Set the freelancer to the current user when creating a proposal."""
        validated_data['freelancer'] = self.context['request'].user
        return super().create(validated_data)

# Alias for backward compatibility
JobSerializer = JobListSerializer
