"""Info for time zones and daylight savings time periods"""

from settings.settings import settings
import time

class Time_Functions:

    def __init__(self):
        # time zone info to adjust UTC time to local time
        self.time_zone_offset = settings.UTC_offset # the adjustment for standard time
        self.daylight_saving_periods = []
        self.daylight_period_setup()

    
    def daylight_period_setup(self):
        """Set up the start and end times for DST.
        Results are in UTC time."""

        # for 2023
        #DTS begins Sunday, March 12, 2023, 2:00:00 am
        #DTS ends Sunday, November 5, 2023, 2:00:00 am
        self.daylight_saving_periods.append((
            (time.mktime((2023,3,12,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            (time.mktime((2023,11,5,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            ))
        # for 2024
        #DTS begins Sunday, March 10, 2024, 2:00:00 am
        #DTS ends Sunday, November 3, 2024, 2:00:00 am
        self.daylight_saving_periods.append((
            (time.mktime((2024,3,10,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            (time.mktime((2024,11,3,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            ))
        # for 2025
        #DTS begins Sunday, March 9, 2025, 2:00:00 am
        #DTS ends Sunday, November 2, 2025, 2:00:00 am
        self.daylight_saving_periods.append((
            (time.mktime((2025,3,9,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            (time.mktime((2025,11,2,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            ))
        

    @property
    def is_daylight_savings(self):
        # Return True if it is daylight savings time else false
        time_seconds = time.mktime(time.localtime())
        # convert to UTC time
        time_seconds += (3600 * self.time_zone_offset)
        
        # check if we are in daylight savings time
        for period in self.daylight_saving_periods:
            if time_seconds >= period[0] and time_seconds <= period[1]:
                # this is the correct period, adjust the time
                return True
        
        return False
