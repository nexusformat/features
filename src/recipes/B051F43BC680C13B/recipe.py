from itertools import compress


class NXlogExamples:
    def __init__(self):
        pass


class _NXlogFinder(object):
    """
    Finds NXevent_data groups in the file
    """

    def __init__(self):
        self.hits = []

    def _visit_NXlog(self, name, obj):
        if "NX_class" in obj.attrs.keys():
            if "NXlog" in obj.attrs["NX_class"]:
                self.hits.append(obj)

    def get_NXlog(self, nx_file, entry):
        self.hits = []
        nx_file[entry].visititems(self._visit_NXlog)
        return self.hits


def validate(nx_log):
    """
    Checks that lengths of datasets which should be the same length as each other are.

    :param nx_log: An NXlog group which was found in the file
    """
    fails = []

    _check_datasets_have_same_length(nx_log, ['cue_timestamp_zero', 'cue_index'], fails)
    if 'time' in nx_log:
        if 'value' in nx_log:
            if nx_log['value'].size()[0] != nx_log['time'].size()[0]:
                fails.append(
                    'The first dimension of the value dataset should have the '
                    'same size as the time dataset in ' + nx_log.name)
        if 'raw_value' in nx_log:
            if nx_log['raw_value'].size()[0] != nx_log['time'].size()[0]:
                fails.append(
                    'The first dimension of the raw_value dataset should have the '
                    'same size as the time dataset in ' + nx_log.name)

    if len(fails) > 0:
        raise AssertionError('\n'.join(fails))


def _check_datasets_have_same_length(group, dataset_names, fails):
    """
    If all named datasets exist in group then check they have the same length

    :param group: HDF group
    :param dataset_names: Iterable of dataset names
    :param fails: Failures are recorded in this list
    """
    dataset_lengths = [group[dataset_name].len() for dataset_name in _existent_datasets(group, dataset_names)]
    if len(set(dataset_lengths)) > 1:
        fails.append(', '.join(dataset_names) + " should have the same length in " + group.name)


def _existent_datasets(group, dataset_names):
    """
    Reduce dataset list to only those present in the group

    :param group: HDF group containing the datasets
    :param dataset_names: Iterable of dataset names
    :return: List containing only the dataset names which exist in the group
    """
    existant_dataset_mask = [True if dataset_name in group else False for dataset_name in dataset_names]
    return list(compress(dataset_names, existant_dataset_mask))


class recipe:
    """
    NXlog - including examples of using the new cue datasets

    Proposed by: matthew.d.jones@stfc.ac.uk
    """

    def __init__(self, filedesc, entrypath):
        """
        :param filedesc: h5py file object of the NeXus/HDF5 file
        :param entrypath: path of the entry containing this feature
        """
        self.file = filedesc
        self.entry = entrypath
        self.title = "NXlog - including examples of using the new cue datasets"

    def process(self):
        """
        Recipes need to implement this method and return information which
        is useful to a user and instructive to a person reading the code.
        See some of the recommended examples for inspriration what to return.

        :return: the essence of the information recorded in this feature
        """
        nx_log = _NXlogFinder()
        nx_log_list = nx_log.get_NXlog(self.file, self.entry)
        if len(nx_log_list) == 0:
            raise AssertionError("No NXlog entries found")
        for nx_log_entry in nx_log_list:
            validate(nx_log_entry)

        return NXlogExamples
