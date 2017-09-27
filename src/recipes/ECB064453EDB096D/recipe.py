from datetime import datetime, tzinfo, timedelta


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)


def check_nframes(context, nx_event_data, item, fails):
    """
    Check that the length of event_time_zero and event_index are consistent.
    They should both be the number of frames (pulses).
    """
    dataset_length = nx_event_data[item].shape[0]
    if ('event_time_zero' in nx_event_data.keys()) and (nx_event_data['event_time_zero'].shape[0] != dataset_length):
        fails.append("'%s' should have the same number of entries as '%s'" % (item, context['event_time_zero']))


def check_nevents(context, nx_event_data, item, fails):
    """
    Check that the length of the dataset is equal to the total count of events
    """
    dataset_length = nx_event_data[item].shape[0]
    if ('total_counts' in nx_event_data.keys()) and (dataset_length != nx_event_data['total_counts'][...]):
        fails.append(
            "'%s' should have a number of entries matching the total number of events recorded in 'total_counts'"
            % item)


class NXevent_dataExamples:
    def __init__(self):
        pass

    @staticmethod
    def get_pulse_index_of_event(nx_event_data, nth_event):
        """
        Find the pulse index that the nth_event occurred in
        :param: nx_event_data: An NXevent_data group which was found in the file
        :param nth_event: The Nth detection event in the group
        :return: pulse index of the nth_event
        """
        # Find index of the last element which has event_index lower than the nth_event
        # this is the index of the pulse (frame) which the nth_event falls in
        event_index = nx_event_data['event_index'][...]
        for i, event_index_for_pulse in enumerate(event_index):
            if event_index_for_pulse > nth_event:
                return i - 1

    def get_time_neutron_detected(self, nx_event_data, nth_event):
        """
        Use offset and time units attributes to find the absolute time
        that neutron with index of event_number to hit the detector
        :param: nx_event_data: An NXevent_data group which was found in the file
        :param nth_event: The Nth detection event in the group
        :return: Absolute time of neutron event detection in ISO8601 format
        """
        if "event_time_offset" in nx_event_data.keys() and nx_event_data['event_time_offset'][...].size > (
                    nth_event + 1):
            # Get absolute pulse time in seconds since epoch
            pulse_index = self.get_pulse_index_of_event(nx_event_data, nth_event)
            pulse_start_time_seconds = self._convert_to_seconds(nx_event_data['event_time_zero'][pulse_index],
                                                                nx_event_data['event_time_zero'].attrs['units'])
            pulse_start_offset = self._isotime_to_unixtime_in_seconds(nx_event_data['event_time_zero'].attrs['offset'])
            pulse_absolute_seconds = pulse_start_time_seconds + pulse_start_offset

            # Get event time in seconds relative to pulse time
            event_offset = nx_event_data['event_time_offset'][nth_event]
            event_offset_seconds = self._convert_to_seconds(event_offset,
                                                            nx_event_data['event_time_offset'].attrs['units'])

            # Calculate absolute event time in seconds since epoch
            absolute_event_time_seconds = pulse_absolute_seconds + event_offset_seconds
            # and convert to a readable string in ISO8601 format
            absolute_event_time_iso = datetime.fromtimestamp(absolute_event_time_seconds, tz=UTC()).isoformat()
            return absolute_event_time_iso

    def get_slice_of_events_by_time(self, nx_event_data, event_index):
        """
        Get cued slice of events which includes the event index specified.

        cue_index and cue_timestamp_zero allow easy efficient access to a slice of event
        data between two timestamps. This slice might, for example, correspond to when a
        control parameter was changed or data which were received from a network stream
        in a single message.

        :param nx_event_data: An NXevent_data group which was found in the file
        :param event_index: event_index which falls inside the range for a cued slice of events
        :return: tuple of lists of event_id and event_time_offset for events in a cued slice
        """
        # Find cue entry which falls just before the event_index we are looking for
        cue_i = self._get_last_index_before_larger_than_target(nx_event_data['cue_index'], event_index)
        # Index range of slice
        start_i = nx_event_data['cue_index'][cue_i]
        end_i = nx_event_data['cue_index'][cue_i + 1]
        return nx_event_data['event_id'][start_i:end_i], nx_event_data['event_time_offset'][start_i:end_i]

    @staticmethod
    def _get_last_index_before_larger_than_target(search_dataset, target, start_index=0, end_index=-1):
        """
        Find the index of the last element in the search_dataset which has a value
        smaller than target.
        Search space can be reduced with start_index and end_index to avoid
        loading the entire dataset from file. Event datasets are often larger
        than available memory.
        :param search_dataset: dataset to search
        :param target: target value
        :param start_index: index to start searching at
        :param end_index: index to search until
        :return: last index before the value exceeds the target
        """
        last_i = 0
        for i, value in enumerate(search_dataset[start_index:end_index]):
            if target > value:
                return max(0, (i + start_index) - 1)
            last_i = i
        return last_i - 1

    @staticmethod
    def _isotime_to_unixtime_in_seconds(isotime):
        utc_dt = datetime.strptime(isotime, '%Y-%m-%dT%H:%M:%S')
        # convert UTC datetime to seconds since the Epoch
        return (utc_dt - datetime(1970, 1, 1)).total_seconds()

    @staticmethod
    def _convert_to_seconds(event_offset, time_unit):
        if time_unit in ['seconds', 'second', 's']:
            return event_offset
        elif time_unit in ['milliseconds', 'millisecond', 'ms']:
            return event_offset * 1e-3
        elif time_unit in ['microseconds', 'microsecond', 'us']:
            return event_offset * 1e-6
        elif time_unit in ['nanoseconds', 'nanosecond', 'ns']:
            return event_offset * 1e-9
        else:
            raise ValueError('Unrecognised time unit in event_time_offset')


VALIDATE = {
    "total_counts": [],
    "event_id": [check_nevents],
    "event_index": [check_nframes],
    "event_time_offset": [check_nevents],
    "event_time_zero": []
}


class _NXevent_dataFinder(object):
    """
    Finds NXevent_data groups in the file
    """

    def __init__(self):
        self.hits = []

    def _visit_NXevent_data(self, name, obj):
        if "NX_class" in obj.attrs.keys():
            if "NXevent_data" in obj.attrs["NX_class"]:
                self.hits.append(obj)

    def get_NXevent_data(self, nx_file, entry):
        self.hits = []
        nx_file[entry].visititems(self._visit_NXevent_data)
        return self.hits


def validate(nx_event_data):
    """
    Checks that fields which should be present are, and that lengths of datasets
    are consistent with each other and the total count of events.

    :param nx_event_data: An NXevent_data group which was found in the file
    """

    context = {}
    fails = []

    for item in VALIDATE.keys():
        if item not in nx_event_data.keys():
            fails.append("'%s' is missing from the NXevent_data entry" % item)
        else:
            for test in VALIDATE[item]:
                test(context, nx_event_data, item, fails)

    if len(fails) > 0:
        raise AssertionError('\n'.join(fails))


class recipe:
    """
        This is meant to help consumers of this feature to understand how to implement
        code that understands that feature (copy and paste of the code is allowed).
        It also documents in what preference order (if any) certain things are evaluated
        when finding the information.
    """

    def __init__(self, filedesc, entrypath):
        self.file = filedesc
        self.entry = entrypath
        self.title = "NXevent_data"

    def process(self):
        nx_event_data = _NXevent_dataFinder()
        nx_event_data_list = nx_event_data.get_NXevent_data(self.file, self.entry)
        if len(nx_event_data_list) == 0:
            raise AssertionError("No NXevent_data entries found")
        for nx_event_data_entry in nx_event_data_list:
            validate(nx_event_data_entry)

        return NXevent_dataExamples
