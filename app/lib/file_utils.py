import os

def make_path(filespec):
    """
    Test the filespec path and if not found, create the path
    but not the file if a file name is included in the path.
    Returns True if either the path already existed or was
    created.
    
    The filespec must always begin with a / and describe the
    full path to be created.
    
    If the filespec does not end in a / the last element is assumed
    to be the file name and it is discarded.
    
    """
    
    # for this simple version, alway start from root
    if not filespec or not filespec[0] == '/':
        raise AssertionError('filespec must begin with a slash')
        
    # save the current working dir
    save_dir = os.getcwd()
    out = True
    
    # split it into directories and create them if needed
    path_list = filespec.split("/")
    if path_list and path_list[0] == '':
        path_list[0] = '/'
        
    if path_list and not path_list[-1].endswith('/'):
        path_list.pop() # remove the file name element
        
    current_path= path_list[0]
    try:
        for d in path_list:
            os.chdir(current_path)
            if d != '/' and not d in os.listdir():
                os.mkdir(d)
                
            current_path = join_path(current_path,d)
    except Exception as e:
        print(f'Unable to create path: {current_path}',str(e))
        out = False
    
    os.chdir(save_dir) # restore the working dir
    return out


def join_path(base,add):
    """Roughly replicate python os.path.join"""
    
    out = (base + '/' + add).replace('//','/')
        
    return out


def is_dir(node):
    """return true if node name is in the current working
direcory and it is a directory itself.

    node may be a path."""
    
    path = ''
    if '/' in node:
        path = node.rstrip('/')
        i = path.rfind('/')
        if i < 0:
            node = path
            path = ''
        else:
            node = path[i+1:]
            path = path[:i+1]

    d = os.ilistdir(path)
    for e in d:
        if node == e[0]:
            if e[1] == 0x4000:
                return True
            break
        
    return False


def delete_all(path):
    """Delete all nodes in the last element of the path.
    if the last element in the path is a directory
    delete all down to and including that directory.

    If the last element in path is not a directory, delete only that node.
        
    path must orginate at the root directory '/'
    
    Return True if successful
    
    """
    
    out = True

    if not path or path[0] != '/': return False

    path_list = path.split('/')

    if not path_list: return False
    
    path_list.pop(0) # remove the root reference

    if not path_list: return out # dont delete the root dir

    try:
        current_path = '/' + '/'.join(path_list)
        if is_dir(current_path):
            file_list = os.listdir(current_path)
            for f in file_list:
                delete_all(join_path(current_path,f))
            os.rmdir(current_path)
            path_list.pop()
        else:
            os.remove(current_path)
    except Exception as e:
        out = False
       
    return out    
