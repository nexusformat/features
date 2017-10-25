#!/usr/bin/python
import h5py

"""
In the linklist I keep the target attribute data from NXdata/data datasets.
This in order to favour datasets in NXdata against stuff scattered over the hierarchy. 
"""
plotlist = []
linklist = []

def visit_nxdata(name,obj):
    if isinstance(obj,h5py.Group):
        try:
            nxclass = obj.attrs['NX_class']
            if nxclass == 'NXdata':
                ds = obj['data']
                if ds.name not in plotlist:
                    plotlist.append(ds.name)
                    try:
                        target = ds.attrs['target']
                        linklist.append(target)
                    except:
                        pass
        except:
            pass



def visit_dataset(name,obj):
    if isinstance(obj,h5py.Dataset):
        try:
            sig = obj.attrs['signal']
            if obj.name not in linklist and obj.name not in plotlist:
                plotlist.append(obj.name)
        except:
            pass
                

class recipe:
    """
    Find plottable data

    Proposed by: mark.koennecke@psi.ch

    Tries to locate the plotable data in the file. Raises an exception if it cannot find any. 
    Else gives you a list of paths with plotable data and a score. 

    """

    def find_plotable_data(self):
        plotlist = []
        linklist = []
        self.file[self.entry].visititems(visit_nxdata)
        return self.file[self.entry].visititems(visit_dataset)

    def __init__(self, filedesc, entrypath):
        self.file = filedesc
        self.entry = entrypath
        self.title = "Find plotable data"

    def process(self):
        self.find_plotable_data()
        if len(plotlist) > 0:
            return plotlist
        else:
            raise AssertionError("There is no plotable data in this entry in this file.")

if __name__ == '__main__':
    import sys
    import h5py

    handle = h5py.File(sys.argv[1])

    r = recipe(handle, '/')
    res = r.process()
    print(res)
