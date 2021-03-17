import os


def get_file_by_extension(extension, folder='models'):
    files = os.listdir(f"./{folder}")
    files = list(filter(lambda x: x.endswith(extension), files))

    if len(files) > 1:
        raise ValueError(f"More than one file with extension *.{extension}. {files}")
    else:
        return f"./{folder}/{files[0]}"