from datetime import datetime, tzinfo, timedelta
import numpy as np
from itertools import compress


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)


class NXevent_dataExamples:
    def __init__(self, nx_event_data):
        self.nx_event_data = nx_event_data

    def get_pulse_index_of_event(self, nth_event):
        """
        Find the pulse index that the nth_event occurred in

        :param nth_event: The Nth detection event in the group
        :return: pulse index of the nth_event
        """
        # Find index of the last element which has event_index lower than the nth_event
        # this is the index of the pulse (frame) which the nth_event falls in
        event_index = self.nx_event_data['event_index'][...]
        for i, event_index_for_pulse in enumerate(event_index):
            if event_index_for_pulse > nth_event:
                return i - 1

    def get_time_neutron_detected(self, nth_event):
        """
        Use offset and time units attributes to find the absolute time
        that neutron with index of event_number to hit the detector

        :param nth_event: The Nth detection event in the group
        :return: Absolute time of neutron event detection in ISO8601 format
        """
        if "event_time_offset" in self.nx_event_data.keys() and self.nx_event_data['event_time_offset'][...].size > (
                    nth_event + 1):
            # Get absolute pulse time in seconds since epoch
            pulse_index = self.get_pulse_index_of_event(nth_event)
            pulse_start_time_seconds = self._convert_to_seconds(self.nx_event_data['event_time_zero'][pulse_index],
                                                                self.nx_event_data['event_time_zero'].attrs['units'])
            pulse_start_offset = self._isotime_to_unixtime_in_seconds(
                self.nx_event_data['event_time_zero'].attrs['offset'])
            pulse_absolute_seconds = pulse_start_time_seconds + pulse_start_offset

            # Get event time in seconds relative to pulse time
            event_offset = self.nx_event_data['event_time_offset'][nth_event]
            event_offset_seconds = self._convert_to_seconds(event_offset,
                                                            self.nx_event_data['event_time_offset'].attrs['units'])

            # Calculate absolute event time in seconds since epoch
            absolute_event_time_seconds = pulse_absolute_seconds + event_offset_seconds
            # and convert to a readable string in ISO8601 format
            absolute_event_time_iso = datetime.fromtimestamp(absolute_event_time_seconds, tz=UTC()).isoformat()
            return absolute_event_time_iso

    def get_events_by_time_range(self, range_start, range_end):
        """
        Return arrays of neutron detection timestamps and the corresponding IDs for the detectors on which they
        were detected, for a given time range.
        Note, method uses (the optional) event_time_zero and event_index to achieve this without loading entire
        event datasets which in general can be too large to fit in memory.

        :param range_start: Start time range in seconds measured from the same reference as the pulse times
        :param range_end: End time range in seconds measured from the same reference as the pulse times
        :return: Detection event times and detector ids
        """
        # event_time_zero is a small subset of timestamps from the full event_time_offsets dataset
        # Since it is small we can load the whole dataset from file with [...]
        cue_timestamps = self.nx_event_data['event_time_zero'][...]
        # event_index maps between indices in event_time_zero and event_time_offsets
        cue_indices = self.nx_event_data['event_index'][...]

        # Look up the positions in the full timestamp list where the cue timestamps are in our range of interest
        range_indices_all = cue_indices[np.append((range_start < cue_timestamps[1:]), [True]) &
                                        np.append([True], (range_end > cue_timestamps[:-1]))]
        range_indices = range_indices_all[[0, -1]]
        range_timestamps_all = cue_timestamps[np.append((range_start < cue_timestamps[1:]), [True]) &
                                              np.append([True], (range_end > cue_timestamps[:-1]))]

        # Now we can extract a slice of the log which we know contains the time range we are interested in
        times = self.nx_event_data['event_time_offset'][range_indices[0]:range_indices[1]]
        detector_ids = self.nx_event_data['event_id'][range_indices[0]:range_indices[1]]

        # Convert everything to seconds
        event_time_units = self.nx_event_data['event_time_offset'].attrs.get('units')
        pulse_time_units = self.nx_event_data['event_time_zero'].attrs.get('units')
        times = self._convert_to_seconds(times.astype(np.float64), event_time_units)
        range_timestamps_all = self._convert_to_seconds(range_timestamps_all.astype(np.float64), pulse_time_units)

        # Add the pulse times to the event times to give an "absolute" time for each event
        new_range_indices = np.array(range_indices_all) - range_indices_all[0]
        times_list = []
        for i in range(len(new_range_indices) - 1):
            times_list.append(times[new_range_indices[i]:new_range_indices[i + 1]] + range_timestamps_all[i])

        # Sort the absolute times (times in each pulse are not sorted) and rearrange the detector id list accordingly
        absolute_times = np.concatenate(times_list)
        sort_order = np.argsort(absolute_times)
        absolute_times = absolute_times[sort_order]
        detector_ids = detector_ids[sort_order]

        # Truncate them to the exact time range asked for
        absolute_times_mask = (range_start <= absolute_times) & (absolute_times <= range_end)
        absolute_times = absolute_times[absolute_times_mask]
        detector_ids = detector_ids[absolute_times_mask]

        return absolute_times, detector_ids

    @staticmethod
    def _isotime_to_unixtime_in_seconds(isotime):
        utc_dt = datetime.strptime(isotime, '%Y-%m-%dT%H:%M:%S')
        # convert UTC datetime to seconds since the Epoch
        return (utc_dt - datetime(1970, 1, 1)).total_seconds()

    @staticmethod
    def _convert_to_seconds(timestamps, time_unit):
        """
        Convert a single time value or numpy array of times to seconds

        :param timestamps: Time or array to times to convert
        :param time_unit: Units of the time to convert from
        :return: Time or times in seconds
        """

        def _convert_single_timestamp_to_seconds(timestamp):
            if time_unit in ['seconds', 'second', 's']:
                return timestamp
            elif time_unit in ['milliseconds', 'millisecond', 'ms']:
                return timestamp * 1e-3
            elif time_unit in ['microseconds', 'microsecond', 'us']:
                return timestamp * 1e-6
            elif time_unit in ['nanoseconds', 'nanosecond', 'ns']:
                return timestamp * 1e-9
            else:
                raise ValueError('Unrecognised time unit in event_time_offset')

        if isinstance(timestamps, np.ndarray):
            vectorised_convert_single_timestamp_to_seconds = np.vectorize(_convert_single_timestamp_to_seconds,
                                                                          otypes=[np.float64])
            return vectorised_convert_single_timestamp_to_seconds(timestamps)
        else:
            return _convert_single_timestamp_to_seconds(timestamps)

    def __str__(self):
        return "Valid NXevent_data group at " + self.nx_event_data.name + \
               " containing " + str(self.nx_event_data['event_id'].len()) + " events"

    __repr__ = __str__


class _NXevent_dataFinder(object):
    """
    Finds NXevent_data groups in the file
    """

    def __init__(self):
        self.hits = []

    def _visit_NXevent_data(self, name, obj):
        if "NX_class" in obj.attrs.keys():
            if "NXevent_data" == str(obj.attrs["NX_class"], 'utf8'):
                self.hits.append(obj)

    def get_NXevent_data(self, nx_file, entry):
        self.hits = []
        nx_file[entry].visititems(self._visit_NXevent_data)
        return self.hits


def validate(nx_event_data):
    """
    Checks that lengths of datasets which should be the same length as each other are.

    :param nx_event_data: An NXevent_data group which was found in the file
    """
    fails = []

    _check_datasets_have_same_length(nx_event_data, ['event_time_offset', 'event_id'], fails)
    _check_datasets_have_same_length(nx_event_data, ['event_time_zero', 'event_index'], fails)
    _check_datasets_have_same_length(nx_event_data, ['cue_timestamp_zero', 'cue_index'], fails)

    if len(fails) > 0:
        raise AssertionError('\n'.join(fails))


def _check_datasets_have_same_length(group, dataset_names, fails):
    """
    If all named datasets exist in group then check they have the same length

    :param group: HDF group
    :param dataset_names: Iterable of dataset names
    :param fails: Failures are recorded in this list
    """
    dataset_lengths = [group[dataset_name].len() for dataset_name in _existant_datasets(group, dataset_names)]
    if len(set(dataset_lengths)) > 1:
        fails.append(', '.join(dataset_names) + " should have the same length in " + group.name)


def _existant_datasets(group, dataset_names):
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
        examples = []
        for nx_event_data_entry in nx_event_data_list:
            validate(nx_event_data_entry)
            examples.append(NXevent_dataExamples(nx_event_data_entry))

        return examples
