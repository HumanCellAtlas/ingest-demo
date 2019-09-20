from .entity_summary import EntitySummary
from .submission_summary import SubmissionSummary


class ProjectSummary:

    def __init__(self):
        self.biomaterial_summary = EntitySummary()
        self.protocol_summary = EntitySummary()
        self.process_summary = EntitySummary()
        self.file_summary = EntitySummary()

        self.submission_status = None
        self.create_date = None
        self.last_updated_date = None

    def add_submission_summary(self, submission_summary: 'SubmissionSummary') -> 'ProjectSummary':
        """
        Adds a submission summary to this project summary
        :param submission_summary: SubmissionSummary to add to self
        :return: self
        """
        self.biomaterial_summary += submission_summary.biomaterial_summary
        self.protocol_summary += submission_summary.protocol_summary
        self.process_summary += submission_summary.process_summary
        self.file_summary += submission_summary.file_summary

        return self
