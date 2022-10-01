import io
from pickletools import genops
from typing import Optional


class InvalidMagicError(Exception):
    def __init__(self, provided_magic: Optional[int], magic:int):
        self.provided_magic = provided_magic
        self.magic = magic
        super().__init__()

    def __str__(self) -> str:
        return f"{self.provided_magic} != {self.magic}"


# copied from pytorch code
MAGIC_NUMBER = 0x1950a86a20f9469cfc6c


# copied from pytorch code
def _is_compressed_file(f) -> bool:
    compress_modules = ['gzip']
    try:
        return f.__module__ in compress_modules
    except AttributeError:
        return False


# copied from pytorch code
def _should_read_directly(f):
    """
    Checks if f is a file that should be read directly. It should be read
    directly if it is backed by a real file (has a fileno) and is not a
    a compressed file (e.g. gzip)
    """
    if _is_compressed_file(f):
        return False
    try:
        return f.fileno() >= 0
    except io.UnsupportedOperation:
        return False
    except AttributeError:
        return False


def _is_zipfile(f) -> bool:
    # This is a stricter implementation than zipfile.is_zipfile().
    # zipfile.is_zipfile() is True if the magic number appears anywhere in the
    # binary. Since we expect the files here to be generated by torch.save or
    # torch.jit.save, it's safe to only check the start bytes and avoid
    # collisions and assume the zip has only 1 file.
    # See bugs.python.org/issue28494.

    # Read the first 4 bytes of the file
    read_bytes = []
    start = f.tell()

    byte = f.read(1)
    while byte != "":
        read_bytes.append(byte)
        if len(read_bytes) == 4:
            break
        byte = f.read(1)
    f.seek(start)

    local_header_magic_number = [b'P', b'K', b'\x03', b'\x04']
    return read_bytes == local_header_magic_number


def get_magic_number(data: io.BytesIO) -> Optional[int]:
    for opcode, args, _pos in genops(data):
        if "INT" in opcode.name or "LONG" in opcode.name:
            return int(args)
    return None

