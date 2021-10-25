from django.test.testcases import TestCase
import ddt
from mock import Mock, patch
from contextlib import contextmanager

from openassessment.staffgrader.serializers.submission_list import (
    SubmissionListSerializer, SubmissionListItemSerializer, SubmissionListItemScoreSerializer
)

class BaseSerializerTest(TestCase):

    def setUp(self):
        super().setUp()
        self.maxDiff = None


@ddt.ddt
class TestSubmissionListItemScoreSerializer(BaseSerializerTest):

    @ddt.unpack
    @ddt.data((1, 10), (99, 100), (0, 0))
    def test_serializer(self, earned, possible):
        mock_assessment = Mock(points_earned=earned, points_possible=possible)
        self.assertDictEqual(
            SubmissionListItemScoreSerializer(mock_assessment).data,
            {
                'pointsEarned': mock_assessment.points_earned,
                'pointsPossible': mock_assessment.points_possible
            }
        )
    

@ddt.ddt
class TestSubmissionListItemSerializer(BaseSerializerTest):

    @contextmanager
    def mock_get_gradedBy(self):
        with patch.object(SubmissionListItemSerializer, 'get_gradedBy', return_value='get_gradedBy'):
            yield
    
    @contextmanager
    def mock_get_username(self):
        with patch.object(SubmissionListItemSerializer, 'get_username', return_value='get_username'):
            yield

    @contextmanager
    def mock_get_score(self):
        with patch.object(SubmissionListItemSerializer, 'get_score', return_value='get_score'):
            yield


    def test_serializer(self):
        mock_workflow = Mock()
        with self.mock_get_gradedBy():
            with self.mock_get_username():
                with self.mock_get_score():
                    result = SubmissionListItemSerializer(mock_workflow).data
        self.assertDictEqual(
            result,
            {
                'submissionUuid': str(mock_workflow.submission_uuid),
                'dateSubmitted': str(mock_workflow.created_at),
                'dateGraded': str(mock_workflow.grading_completed_at),
                'gradingStatus': str(mock_workflow.grading_status),
                'lockStatus': str(mock_workflow.lock_status),
                'gradedBy': 'get_gradedBy',
                'username': 'get_username',
                'score': 'get_score',
            }
        )

    @ddt.data(True, False)   
    def test_get_gradedBy(self, has_scorer_id):
        mock_workflow = Mock()
        scorer_id, scorer_username = 'test_scorer_id', 'test_scorer_username'
        if has_scorer_id:
            mock_workflow.scorer_id = scorer_id
        else:
            mock_workflow.scorer_id = None
    
        with self.mock_get_username():
            with self.mock_get_score():
                result = SubmissionListItemSerializer(
                    mock_workflow,
                    context={
                        'anonymous_ids_to_usernames': {scorer_id: scorer_username}
                    }
                ).data
        if has_scorer_id:
            self.assertEqual(result['gradedBy'], scorer_username)
        else:
            self.assertIsNone(result['gradedBy'])

    @ddt.data(True, False)   
    def test_get_score(self, has_assessment):
        mock_workflow = Mock()
        # mock_workflow.identifying_uuid = str(mock_workflow.identifying_uuid)
        mock_assessment = Mock()
    
        mock_assessments_by_submission_uuid = {}
        if has_assessment:
            mock_assessments_by_submission_uuid[mock_workflow.identifying_uuid] = mock_assessment

        with self.mock_get_username():
            with self.mock_get_gradedBy():
                with patch(
                    'openassessment.staffgrader.serializers.submission_list.SubmissionListItemScoreSerializer'
                ) as mock_score_serializer:
                    result = SubmissionListItemSerializer(
                        mock_workflow,
                        context={
                            'assessments_by_submission_uuid': mock_assessments_by_submission_uuid
                        }
                    ).data

        if has_assessment:
            mock_score_serializer.assert_called_once_with(mock_assessment)
            self.assertEqual(result['score'], mock_score_serializer.return_value.data)
        else:
            self.assertIsNone(result['score'])
    
    def test_get_username(self):
        mock_workflow = Mock()
        # mock_workflow.identifying_uuid = str(mock_workflow.identifying_uuid)
        student_id, username = 'test_student_id', 'test_username'

        with self.mock_get_score():
            with self.mock_get_gradedBy():
                result = SubmissionListItemSerializer(
                    mock_workflow,
                    context={
                        'submission_uuids_to_student_id': {mock_workflow.identifying_uuid: student_id},
                        'anonymous_ids_to_usernames': {student_id: username}
                    }
                ).data

        self.assertEqual(result['username'], username)


class TestSubmissionListSerializer(BaseSerializerTest):

    def test_serializer(self):
        # Make three workflows. The first two have scorer_ids and the third does not
        workflows = [
            Mock(scorer_id='staff_student_id_1'),
            Mock(scorer_id='staff_student_id_2'),
            Mock(scorer_id=None)
        ]

        # Dict from workflow uuids to student_id_{0,1,2}
        submission_uuids_to_student_id = {
            workflow.identifying_uuid: f'student_id_{i}'
            for i, workflow in enumerate(workflows)
        }
        
        # Simple mapping of student_id_n to username_n
        anonymous_ids_to_usernames = {
            'student_id_{i}': 'username_{i}'
            for i in range(3)
        }
        # also include usernames for the scorers of the first two workflows
        anonymous_ids_to_usernames[workflows[0].scorer_id] = 'staff_username_1'
        anonymous_ids_to_usernames[workflows[0].scorer_id] = 'staff_username_2'

        # Add assessments for the "scored" workflows
        assessments_by_submission_uuid = {
            workflows[0].identifying_uuid: Mock(points_possible=20, points_earned=10),
            workflows[1].identifying_uuid: Mock(points_possible=20, points_earned=7),
        }

        data = SubmissionListSerializer(
            {'submissions': {workflow.identifying_uuid: workflow for workflow in workflows}},
            context={
                'submission_uuids_to_student_id': submission_uuids_to_student_id,
                'anonymous_ids_to_usernames': anonymous_ids_to_usernames,
                'assessments_by_submission_uuid': assessments_by_submission_uuid,
            }
        ).data

        self.assertDictEqual(
            data['submissions'],
            {
                workflows[0].identifying_uuid: {
                    'submissionUuid': str(workflows[0].submission_uuid),
                    'dateSubmitted': str(workflows[0].created_at),
                    'dateGraded': str(workflows[0].grading_completed_at),
                    'gradingStatus': str(workflows[0].grading_status),
                    'lockStatus': str(workflows[0].lock_status),
                    'gradedBy': 'staff_username_1',
                    'username': 'username_0',
                    'score': {
                        'pointsEarned': 10,
                        'pointsPossible': 20,
                    },
                },
                workflows[1].identifying_uuid: {
                    'submissionUuid': str(workflows[1].submission_uuid),
                    'dateSubmitted': str(workflows[1].created_at),
                    'dateGraded': str(workflows[1].grading_completed_at),
                    'gradingStatus': str(workflows[1].grading_status),
                    'lockStatus': str(workflows[1].lock_status),
                    'gradedBy': 'staff_username_2',
                    'username': 'username_1',
                    'score': {
                        'pointsEarned': 7,
                        'pointsPossible': 20,
                    },
                },
                workflows[2].identifying_uuid: {
                    'submissionUuid': str(workflows[2].submission_uuid),
                    'dateSubmitted': str(workflows[2].created_at),
                    'dateGraded': str(workflows[2].grading_completed_at),
                    'gradingStatus': str(workflows[2].grading_status),
                    'lockStatus': str(workflows[2].lock_status),
                    'gradedBy': 'None',
                    'username': 'username_2',
                    'score': 'None',
                }
            }
        )
