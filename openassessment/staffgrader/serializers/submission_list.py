"""
Serializers for the Submission List endpoint
"""
from rest_framework import serializers


class SubmissionListScoreSerializer(serializers.Serializer):
    pointsEarned = serializers.IntegerField(source='points_earned')
    pointsPossible = serializers.IntegerField(source='points_possible')


class SubmissionListSerializer(serializers.Serializer):
    """
    Serialized info about an item returned from the submission list endpoint
    """
    submissionUuid = serializers.CharField(source='submission_uuid')
    dateSubmitted = serializers.CharField(source='created_at')
    dateGraded = serializers.CharField(source='grading_completed_at')
    gradingStatus = serializers.CharField(source='grading_status')
    lockStatus = serializers.CharField(source='lock_status')
    gradedBy = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    def get_gradedBy(self, workflow):
        if workflow.scorer_id:
            return self.context['anonymous_id_to_username'][workflow.scorer_id]
        else:
            return None

    def get_username(self, workflow):
        student_id = self.context['submission_uuid_to_student_id'][workflow.identifying_uuid]
        return self.context['anonymous_id_to_username'][student_id]

    def get_score(self, workflow):
        assessment = self.context['submission_uuid_to_assessment'].get(workflow.identifying_uuid)
        if assessment:
            return ListStaffWorkflowScoreSerializer(assessment).data
        else:
            return None
