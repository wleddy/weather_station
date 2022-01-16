"""Handle Touch Screen Display """

from ili9341 import Display as ili9341, color565
from machine import Pin
from .xglcd_font import XglcdFont

from .display_setup import get_spi

class Display(ili9341):
    
    FONT_COLOR = WHITE = color565(254,254,254)
    BACKGROUND = BLACK = color565(0,0,0)
    GREEN = color565(81,151,105)
    RED = color565(237,26,27)
    BLUE = color565(59,96,203)
    
    MAX_Y = 319
    MAX_X = 239
    
    def __init__(self,settings,**kwargs):
        
        self.settings = settings
        
        super().__init__(settings.spi,
                         dc=Pin(settings.display_dc),
                         cs=Pin(settings.display_cs),
                         rst=Pin(settings.display_rst),
                         rotation=0,
                         )

        settings.display = self
        
        self.font_path = '/lib/display/fonts/'
        try:
            self.font_path = settings.font_path
        except AttributeError:
            settings.font_path = self.font_path

        self.image_path = '/lib/display/images/'
        try:
            self.image_path = settings.image_path
        except AttributeError:
            settings.image_path = self.image_path

        # provide some reasonable defaults
        # TODO Move to settings
        self.body_font = None
        self.body_font_name = 'Unispace12x24.c'
        self.body_font_width = 12
        self.body_font_height = 24
        self.body_font_spacing = 1
        
        
    def _load_fonts(self):
        # delay the font loading till needed. It takes a while
        
        if not self.body_font:
            # set up the font - Using monospace font for my sanity
            if self.settings.debug: print('Loading fonts...')
            self.body_font_width = 12 # the width of each char in px
            self.body_font_height = 24 # the height in px
            self.body_font_spacing = 1 # space between letters in px
            self.settings.body_font = self.body_font = XglcdFont(self.font_path + self.body_font_name, self.body_font_width, self.body_font_height)
            if self.settings.debug: print('fonts loaded.')
            
        
    def centered_text(self,msg,
                      x=0,
                      y=0,
                      width=None,
                      font=None,
                      color=None,
                      background=None,
                      landscape=True,
                      ):
        """
        Display the msg text centered on the screen or within a region of the
        screen 
        
        x & y should be input as the 'natural' x & y coordinates of the upper left
            corner of the text. That is as if the display is in the normal portrait
            orientation.
            
        The 'natural' 0,0 cordinates are in the upper left corner of the screen
            when the pins are along the top.
            
        If landscape is True, the values will be swapped and adjusted to position
            the text along the long side of the dispaly.
            
        
        x = the distance from the 'top' of the screen to the top of the text. Defaults to top of screen
        y = the distance to the right to offset the first letter. defaults to left edge
        width = the width of the space for text. Defaults to full width
        color = the color for the font. Defaults to FONT_COLOR
        background = the bacground color. Defaults to BACKGROUND
        landscape = True or False. Default True
        font = Xglcfont obj. Defaults to body_font

        """

        if not msg:
            return
        
        if not font:
            self._load_fonts() # Load fonts if not already
            font = self.body_font
        
        if self.settings.debug: print('inital x:{}, y:{}'.format(x,y))

        width = width if width != None else 0 #full width print area
        if self.settings.debug: print('width:',width)
        
        color = color if color != None else self.FONT_COLOR
        background = background if background != None else self.BACKGROUND
        
        # calculate the length of the message in this font
        msg_width = font.measure_text(msg)
        if self.settings.debug: print('msg_width:',msg_width)
        
        final_x = x
        final_y = y
        

        if landscape:
            final_y = self.MAX_Y - x - int((width - msg_width) /2) # left hand edge of print area
            if final_y > self.MAX_Y:
                if self.settings.debug: print('too long at:',final_y + msg_width)
                final_y = self.MAX_Y # too long for display area
            
            final_x = y
            
        if self.settings.debug: print('Calculated final_y:',final_y)
        
        if x + self.body_font_height > self.MAX_X:
            if self.settings.debug: print('too far down at: {}'.format(x))
            x = self.MAX_X - self.body_font_height
            
                    
        self.draw_text(final_x, final_y, msg, font, color,
                                background=background,
                                landscape=True,
                                spacing=self.body_font_spacing,
                               )
        
    
    def show_progress(self,percent):
        # display a progress bar and animation
        # percent is a number between 0 and 100
        w = 18
        x = self.MAX_X - w
        
        if self.settings.debug: print('show_progress. {}'.format(percent))
        
        if percent == 0:
            self.fill_rectangle(x,0,w,self.MAX_Y,self.WHITE)
        else:
            try:
                percent = int(self.MAX_Y * percent / 100) - w #allow room for animation
                self.fill_rectangle(x,self.MAX_Y - percent,w,percent,self.BLACK)
            except Exception as e:
                if self.settings.debug: print('Error in show_progress. {}'.format(str(e)))

class Button:
    """
    a class to describe and display an area on the screen. The area may also
    act as a button and respond to clicks.
    
    A note about screen coordinates:
        The ili9341 controller always works with physical screen locations.
        The 0,0 point is upper left corner of the screen when viewed in
        portrait mode. That is how the Display class handles possitioning.
        
        For Landscape mode the x,y,w,h cordinates have to be manipulated to
        display properly.
        
        When describing screen elements for Landscape viewing, always describe
        them as you would if x,y is now in the upper left when the screen is
        rotated with the pins to the right. This should make it easier to describe
        the screen layout as x is left to right, and y is top to bottom, the same
        as in portrait mode.
    
    Params:
        settings: Settings obj: system settings
        name: str: a (hopfully) unique name
        x: int: x location. Left to right.
        y: int: y location. Top to bottom.
        w: int: width of area. Defaults to full width of screen
        h: int: height of area
        offsets: iterable of ints: top, right, bottom, left offsets to
            calibrate touch to screen display. Defaults to (0,0,0,0,)
        label: str: a text label to display. If set to None no label will be
            displayed. If not provided, the button name will be used.
        font: XglcdFont object: defaults to the system font for the label
        font_color: int: color565 value. default to system font color
        background: int: color565 value. defualts to system background
        landscape: bool: Default True. Landscape or not
        
    Properties:
        margin: int: Default 2. margin to apply to all sides of visible rect of area.
        
    Methods:
        clicked: Return True if a click at point on the screen is within
            the button.
        handle: Override this method to allow special handling of a click event
            within the button instance. May set result property. Should return
            True on success.
        show() Display the area. Return nothing.
    
"""
    def __init__(self,settings,name,x,y,w,h,
                 offsets=None,
                 label = '',
                 font = None,
                 font_color = None,
                 background = None,
                 landscape=True,
                 ):
        
        self.result = None
        self.margin = 2
    
        self.landscape = landscape
        self.settings = settings
        self.display = settings.display
        self.name = name
        self.x = int(x)
        self.y = int(y)
        if not w:
            if self.landscape:
                self.w = self.display.MAX_Y
            else:
                self.w = self.display.MAX_X
        else:
            self.w = int(w)
            
        self.h = int(h)
        
        self.offsets = (0,0,0,0,)
        try:
            if len(offsets) >= 4:
                self.offsets = offsets
        except TypeError:
            pass
        
        if label == None:
            self.label = ''
        elif not label:
            self.label = str(label) if label else self.name
        else:
            self.label = label
            
        try:
            self.font = font if font else self.settings.body_font
        except AttributeError:
            self.font = XglcdFont('/scan_in/display/fonts/Unispace12x24.c', 12, 24)
            self.settings.default_font = self.font
        
        try:
            self.font_color = font_color if font_color != None else settings.font_color
        except AttributeError:
            self.font_color = color565(0,0,255)
            self.settings.default_font_color = self.font_color
        
        try:
            self.background = background if background != None else settings.background
        except AttributeError:
            self.background = color565(100,255,0)
            self.settings.default_background = self.background
        
    def clear(self):
        x,y,w,h = self.get_area_rect()
            
        # graphics are always positioned in the native 'portrait' orientation    
        if self.settings.debug: print('{} rect; x:{}, y:{}, w:{}, h:{}'.format(self.name,x,y,w,h))
        
        self.display.fill_rectangle(x,y,w,h,
                                    color=self.background,
                                    )

            
    def clicked(self,point):
        # determine if a click occured in this button
        # Strangely, the 0,0 point for touch is upper right when
        #   viewed in portrait mode. So the x point needs to be re-interpreted
        result = False
        self.result = None
        
        try:
            click_x = self.display.MAX_X - point[0]
            click_y = point[1]
        except IndexError:
            self.result = 'Index error in {}'.format(point)
            return result
        
        x,y,w,h = self.get_area_rect()
        
        if click_x >= x \
           and click_x <= x + w \
           and click_y >= y \
           and click_y <= y + h:
            result = True
            
        return result


    def handle(self,*args,**kwargs):
        self.result = None
        return False
    
   
    def get_area_rect(self):
        # for landscape display, area coords need to be adjusted
        # to match the native display coords
        if self.landscape:
            # swap the height and width
            w = self.h - self.margin * 2
            h = self.w - self.margin * 2
            x = self.y + self.margin
            # In landscape left hand y is 319
            # move y toward 0 to allow room so h does not overflow display
            y = self.margin
            if self.w < self.display.MAX_Y:
                y = self.display.MAX_Y - self.w - self.x
        else:
            x = self.x + self.margin
            y = self.y + self.margin
            w = self.w - self.margin * 2
            h = self.h - self.margin * 2

        return x,y,w,h,
    
    def show(self):
        # Display a button
        if self.settings.debug: print('{} init; x:{}, y:{}, w:{}, h:{}'.format(self.name,self.x,self.y,self.w,self.h))
        
        self.clear()
        
        # modify x to center text in the vertical space
        text_y = self.y + int((self.h - self.font.height) / 2)
        if text_y < 0:
            text_y = 0
        elif text_y > self.display.MAX_X + self.font.height:
            text_y = self.display.MAX_X - self.font.height

        # provide x and y values for the native orientation
        self.display.centered_text(self.label,
                                x = self.x + self.margin,
                                y = text_y + self.margin,
                                width=self.w - self.margin * 2,
                                font=self.font,
                                color=self.font_color,
                                background=self.background,
                                landscape=self.landscape,
                                )

