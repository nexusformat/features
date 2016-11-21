from abc import ABCMeta, abstractmethod


class SuperRecipe:
    __metaclass__ = ABCMeta
    """
    Recipes should implement this interface, but do not need to subclass SuperRecipe
    """

    @abstractmethod
    def __init__(self, filedesc, entrypath):
        """
        Recipes should implement this method with a descriptive self.title
        :param filedesc: path of the NeXus file
        :param entrypath: path of the feature's directory
        """
        self.file = filedesc
        self.entry = entrypath
        self.title = "Placeholder Title"

    @abstractmethod
    def process(self):
        """
        Recipes should implement this method to return information which is useful to a user
        :return: results of processing this feature
        """
        pass

    @classmethod
    def __subclasshook__(cls, C):
        """
        This method should not be implemented in a recipe
        It allows recipes to be considered a subclass of SuperRecipe without them explicitly subclassing it
        """
        if cls is SuperRecipe:
            if "process" in dir(C):
                return True
        return NotImplemented
