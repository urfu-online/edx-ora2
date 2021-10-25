"""
Serializers for the Submission List endpoint
"""
from rest_framework import serializers


class SubmissionListItemScoreSerializer(serializers.Serializer):
    pointsEarned = serializers.IntegerField(source='points_earned')
    pointsPossible = serializers.IntegerField(source='points_possible')


class SubmissionListItemSerializer(serializers.Serializer):
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
            return self.context['anonymous_ids_to_usernames'][workflow.scorer_id]
        else:
            return None

    def get_username(self, workflow):
        student_id = self.context['submission_uuids_to_student_id'][workflow.identifying_uuid]
        return self.context['anonymous_ids_to_usernames'][student_id]

    def get_score(self, workflow):
        assessment = self.context['assessments_by_submission_uuid'].get(workflow.identifying_uuid)
        if assessment:
            return SubmissionListItemScoreSerializer(assessment).data
        else:
            return None


class SubmissionListSerializer(serializers.Serializer):
    """
    Serializer for the response from the submission list endpoint
    """
    submissions = serializers.DictField(child=SubmissionListItemSerializer())
