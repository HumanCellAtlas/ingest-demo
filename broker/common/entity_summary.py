from collections import OrderedDict


class EntitySummary:
    def __init__(self):
        self.count = 0
        self.breakdown = OrderedDict()

    def __add__(self, other: 'EntitySummary') -> 'EntitySummary':
        """
        adds two EntitySummary together
        :param other:
        :return: self
        """
        # copy self into a new EntitySummary obj
        combined_summary = EntitySummary()
        combined_summary.count = self.count
        combined_summary.breakdown = OrderedDict(self.breakdown)
        
        combined_summary.count += other.count
        for (key, val) in other.breakdown.items():
            if key in combined_summary.breakdown:  # ..do an add
                combined_summary.breakdown[key]['count'] += val['count']
            else:
                combined_summary.breakdown[key] = val

        return combined_summary
