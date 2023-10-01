

def calibration_data(name):
    """Return the calibration data for the specified sensor
        
        A dict containing a list of tuples for each sensor.
        The tuples are organized as:
            0: Raw Sensor temperature
            1: Observed (actual) temperature
            
        The tuples may be in any order but the tempurature values
        must use the same scale as the sensor (f or c)
        
    """
    
    l = {
        'Indoor': [
            (68.2, 65.0),
            (70.2, 66.4),
            (71.6, 66.9),
            (72.3, 68.5),
            (73.0, 67.8),
            (73.6, 68.9),
            (68.5, 65.5),
            (81.1, 78.4),
            (84.9, 82.2),
            ],
        'Outdoor': [
            (37.2, 35.4),
            (46.6, 45.3),
            (43.8, 40.1),
            (53.8, 53.1),
            (51.8, 50.4),
            (57.2, 56.3),
            (90.0, 93.6),
            (89.4, 91.9),
            (95.7, 102.0),
            ],
        }

    return l[name]
