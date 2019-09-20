from unittest import TestCase
from broker.common.submission_summary import SubmissionSummary
from broker.common.project_summary import ProjectSummary


class EntityServiceTest(TestCase):

    def test_add_submission(self):
        project_summary = ProjectSummary()
        submission_summary = SubmissionSummary()

        submission_summary.biomaterial_summary.breakdown['reanimated_donor'] = {'count': 5}
        submission_summary.biomaterial_summary.breakdown['nanomachine'] = {'count': 500}
        submission_summary.biomaterial_summary.count = 505

        submission_summary.protocol_summary.breakdown['next_level_seq_protocol'] = {'count': 3}
        submission_summary.protocol_summary.count = 3

        submission_summary.process_summary.breakdown['wiggle_testtube_process'] = {'count': 11}
        submission_summary.process_summary.count = 11

        submission_summary.file_summary.breakdown['cell_montage_file'] = {'count': 150}
        submission_summary.file_summary.count = 150

        project_summary.add_submission_summary(submission_summary)

        assert project_summary.biomaterial_summary.count == 505
        assert len(project_summary.biomaterial_summary.breakdown.items()) == 2

        assert project_summary.protocol_summary.count == 3
        assert len(project_summary.protocol_summary.breakdown.items()) == 1

        assert project_summary.process_summary.count == 11
        assert len(project_summary.process_summary.breakdown.items()) == 1

        assert project_summary.file_summary.count == 150
        assert len(project_summary.file_summary.breakdown.items()) == 1
