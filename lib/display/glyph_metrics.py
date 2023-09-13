"""
A class to describe the dimensions and some
other info about the digit image files in this 
that are to be used in the weather station display
"""

class Metrics:
    """This is the base class and should probobly not be called directly.
    inherit this into classes for specific image sets"""
    
    def __init__(self,path="/lib/display/images/"):
        self.path = path # full path to the directory containing the images. needs trailing /
        
        self.WIDTH = 48
        self.HEIGHT = 80
        
        # most of the characters will be WIDTH wide
        # some narrower chars are listed here.
        self.DOT_WIDTH = 24
        self.COLON_WIDTH = 24
        self.DASH_WIDTH = 38
        self.ONE_WIDTH = 38
        self.SPACE_WIDTH = 24
                
    def get(self,s):
        """Return a dict containing the full path to the image file
        and the width and height"""
        
        # most images are this size:
        h=self.HEIGHT
        w=self.WIDTH
        c=str(s)
        
        if not isinstance(s,str) or len(s) != 1 or s[0] not in ["0","1","2","3","4","5","6","7","8","9",".","-",":"," ","?"]:
            print("Bad Char:",str(s))
            s="?"

        if s == "1":
            w=self.ONE_WIDTH
        elif s ==".":
            w=self.DOT_WIDTH
            s = "dot"
        elif s == "-":
            w=self.DASH_WIDTH
            s="dash"
        elif s == ":":
            w=self.COLON_WIDTH
            s="colon"
        elif s == " ":
            w=self.SPACE_WIDTH
            s = "space"
        elif s == "?":
            s = "huh"
    
        return {"char":c,"path":self.path + "digit_{}.raw".format(s),"w":w,"h":h,}
        
    def string_width(self,s):
        # return the length of string s when rendered with glyphs
        l = 0
        for x in s:
            l += self.get(x)["w"]
        return l
    
        
class Metrics_80(Metrics):
    """Access the 8m pixel tall glyphs... 
    Really just a psudonym for base class"""
    def __init__(self,path="/lib/display/images/80/"):
        self.path = path
        super().__init__(self.path)
        
        
class Metrics_60(Metrics):
    """Access the 8m pixel tall glyphs... 
    For the smaller sized glyphs"""
    def __init__(self,path="/lib/display/images/60/"):
        self.path = path
        super().__init__(self.path)

        self.WIDTH = 36
        self.HEIGHT = 60
        
        # most of the characters will be WIDTH wide
        # some narrower chars are listed here.
        self.DOT_WIDTH = 18
        self.COLON_WIDTH = 18
        self.DASH_WIDTH = 29
        self.ONE_WIDTH = 29
        self.SPACE_WIDTH = 16
        
class Metrics_78(Metrics):
    """Access the 8m pixel tall glyphs... 
    For the smaller sized glyphs"""
    def __init__(self,path="/lib/display/images/78/"):
        self.path = path
        super().__init__(self.path)

        self.WIDTH = 52
        self.HEIGHT = 78
        
        # most of the characters will be WIDTH wide
        # some narrower chars are listed here.
        self.DOT_WIDTH = 24
        self.COLON_WIDTH = 24
        self.DASH_WIDTH = 42
        self.ONE_WIDTH = 38
        self.SPACE_WIDTH = 26

