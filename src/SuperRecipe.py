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
        :param filedesc:
        :param entrypath:
        """
        self.file = filedesc
        self.entry = entrypath
        self.title = "Placeholder Title"

    @abstractmethod
    def process(self):
        """
        Recipes should implement this method to return ...
        :return:
        """
        return dict()  # should return dict or list here? Or iterable...

    @classmethod
    def __subclasshook__(cls, C):
        """
        This method should not be implemented in a recipe
        :param C:
        :return:
        """
        if cls is SuperRecipe:
            if "process" in dir(C):
                return True
        return NotImplemented
