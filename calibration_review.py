l = {
    'Indoor': [
        (68.2, 65.0),
        (68.5, 65.5),
        (70.2, 66.4),
        (71.6, 66.9),
        (72.3, 68.5),
        (73.6, 68.9),
        (73.0, 67.8),
        ],
    'Outdoor': [
        (37.2, 35.4),
        (43.8, 40.1),
        (46.6, 45.3),
        (51.8, 50.4),
        (53.8, 53.1),
        (57.2, 56.3),
        ],
    }

head = "raw\t|\tactual\t|\tfactor"
for key,value in l.items():
    print(key)
    print(head)
    value.sort()
    for v in value:
        cal = int((v[1]/v[0])*100)/100
        cal = str(cal)[0:4]
        print(v[0],"\t|\t",v[1],"\t|\t",cal)
        